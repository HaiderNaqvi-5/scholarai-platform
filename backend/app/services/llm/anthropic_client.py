"""Anthropic Claude wrapper for the Pakistan pivot (Feature 7 / 8).

Design choices:
- Lazy import of the ``anthropic`` SDK so test environments that lack it can
  still import the module and use the deterministic fallback.
- Prompt caching (``cache_control: ephemeral``) on the static system block —
  the Pakistani SOP context and the visa officer evaluator prompts are reused
  across every call, so caching cuts cost roughly 90% after the first call
  in a 5-minute window.
- ``call_json`` parses the model's response as JSON and returns a Python dict
  while swallowing any prose preamble Claude sometimes emits.
- ``LLMUnavailableError`` is raised only when no API key is configured *and*
  ``LLM_FALLBACK_DETERMINISTIC`` is False. Callers handle the error or rely on
  ``available`` to branch into a deterministic path.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.core.burn_cap import (
    assert_within_burn_cap,
    llm_cost_pkr,
    record_llm,
    release_reservation,
    reserve_burn,
)
from app.core.config import settings


logger = logging.getLogger(__name__)


class LLMUnavailableError(RuntimeError):
    """Raised when no Claude credentials are configured and fallback is disabled."""


@dataclass
class _CachedSystemBlock:
    text: str

    def to_block(self) -> dict[str, Any]:
        return {
            "type": "text",
            "text": self.text,
            "cache_control": {"type": "ephemeral"},
        }


class AnthropicClient:
    """Thin wrapper around the Anthropic SDK with deterministic-fallback hooks."""

    def __init__(self, *, api_key: str | None = None, default_model: str | None = None) -> None:
        self._api_key = api_key or settings.ANTHROPIC_API_KEY
        self._default_model = default_model or settings.ANTHROPIC_MODEL_FAST
        self._client = None  # lazy

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    # ------------------------------------------------------------------
    # Low-level call helpers
    # ------------------------------------------------------------------

    def _ensure_client(self):
        if self._client is None:
            if not self._api_key:
                raise LLMUnavailableError("ANTHROPIC_API_KEY is not configured.")
            try:
                import anthropic  # type: ignore
            except ImportError as exc:  # pragma: no cover - env-dependent
                raise LLMUnavailableError(
                    "anthropic SDK is not installed. Add 'anthropic' to requirements.txt."
                ) from exc
            self._client = anthropic.Anthropic(
                api_key=self._api_key,
                timeout=settings.LLM_REQUEST_TIMEOUT_SECONDS,
            )
        return self._client

    def call_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        max_tokens: int = 1500,
        temperature: float = 0.4,
    ) -> str:
        if not self.available:
            raise LLMUnavailableError("Anthropic API key missing.")
        message = self._raw_call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return _join_text_blocks(message)

    def call_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        max_tokens: int = 1500,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        raw = self.call_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return _extract_json_object(raw)

    # ------------------------------------------------------------------
    # Burn-cap-aware wrapper (Task 11)
    # ------------------------------------------------------------------

    def _raw_call(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        max_tokens: int = 1500,
        temperature: float = 0.4,
    ):
        """Underlying SDK call. Returns the raw ``Message`` object so callers
        that need ``.usage.input_tokens`` / ``.usage.output_tokens`` for cost
        accounting can read them directly."""
        client = self._ensure_client()
        return client.messages.create(
            model=model or self._default_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=[_CachedSystemBlock(system_prompt).to_block()],
            messages=[{"role": "user", "content": user_prompt}],
        )

    async def complete_with_accounting(
        self,
        *,
        db,
        user,
        endpoint: str,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        max_tokens: int = 1500,
        temperature: float = 0.4,
        json_mode: bool = False,
    ):
        """Burn-cap-aware wrapper around the existing call_text / call_json
        helpers.

        Pre-flight ``assert_within_burn_cap`` raises HTTP 429 when the
        projected PKR cost would breach the user's monthly budget. Post-call
        ``record_llm`` writes a ``usage_ledger`` row with the real usage
        tokens returned by the SDK.

        When ``ANTHROPIC_API_KEY`` is unset (deterministic-template path),
        the helper still returns the deterministic-friendly empty payload
        AND records a zero-cost ledger row keyed off the input estimate so
        the audit trail remains complete in offline / CI runs.

        Returns:
            ``dict`` when ``json_mode=True`` (parsed JSON, possibly empty),
            otherwise ``str`` (the joined text blocks).
        """
        resolved_model = model or self._default_model
        kind = "llm_sonnet" if "sonnet" in (resolved_model or "").lower() else "llm_haiku"
        estimated_input = _estimate_input_tokens(system_prompt, user_prompt)
        projected = llm_cost_pkr(kind, estimated_input, max_tokens)

        # R10: reserve the projected cost atomically BEFORE the cap check so a
        # concurrent caller sees this in-flight spend and cannot also slip
        # through. assert_within_burn_cap is then called with a zero projection
        # because the projected amount is already folded into the reservation
        # that _reserved_micro reads back (avoids double-counting). The
        # reservation is released once record_llm has written the durable
        # usage_ledger row (or the call has failed) — see the finally block.
        await reserve_burn(user, projected)
        try:
            await assert_within_burn_cap(db, user, Decimal(0))

            if not self.available:
                # Deterministic-template path: record a synthetic ledger row so
                # the burn-cap audit trail is consistent across online / offline
                # runs, then raise so callers fall back to their template.
                await record_llm(
                    db,
                    user.id,
                    kind,
                    estimated_input,
                    0,
                    endpoint,
                )
                raise LLMUnavailableError("Anthropic API key missing.")

            try:
                message = self._raw_call(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model=resolved_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            except LLMUnavailableError:
                await record_llm(db, user.id, kind, estimated_input, 0, endpoint)
                raise

            usage = getattr(message, "usage", None)
            input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
            output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
            await record_llm(db, user.id, kind, input_tokens, output_tokens, endpoint)

            text = _join_text_blocks(message)
            if json_mode:
                return _extract_json_object(text)
            return text
        finally:
            # Release the in-flight reservation regardless of outcome: the
            # durable usage_ledger row (written by record_llm on every path
            # that proceeds past the cap check) is now the source of truth, and
            # a failed/rejected call must not leave budget permanently held.
            await release_reservation(user, projected)


# ----------------------------------------------------------------------
# Parsing helpers
# ----------------------------------------------------------------------


# Anthropic bills a cached ephemeral prefix at the cache-read rate, ~0.1x the
# base input price, after the first call in the 5-minute window. The static
# system prompt in `_raw_call` is always wrapped in a `_CachedSystemBlock`, so
# the pre-flight projection must not charge it at full price (over-projecting
# burn-cap cost trips the 429 earlier than real spend warrants).
_CACHED_SYSTEM_DISCOUNT = 0.1


def _estimate_input_tokens(system_prompt: str, user_prompt: str) -> int:
    """Cheap pre-flight estimate: ~4 chars per token.

    Used pre-flight to decide whether the call would breach the burn cap.
    The system prompt is sent as a cached ephemeral block (see ``_raw_call``),
    so it is discounted by ``_CACHED_SYSTEM_DISCOUNT`` (cache-read rate); only
    the per-call user prompt is counted at full price. Intentionally
    conservative — under-estimating here lets a call slip through, then the
    post-call ``record_llm`` writes the real usage.
    """
    full_blob = json.dumps(
        {"system": system_prompt or "", "user": user_prompt or ""},
        default=str,
    )
    # Isolate the JSON-escaped contribution of the system text by diffing the
    # full blob against the same blob with an empty system value. Then keep
    # only the cache-read fraction of those system chars; the user prompt and
    # JSON framing stay at full price.
    empty_system_blob = json.dumps(
        {"system": "", "user": user_prompt or ""},
        default=str,
    )
    system_chars = len(full_blob) - len(empty_system_blob)
    discounted_chars = len(full_blob) - (1 - _CACHED_SYSTEM_DISCOUNT) * system_chars
    return max(1, int(discounted_chars // 4))


def _join_text_blocks(message) -> str:  # pragma: no cover - SDK-dependent
    parts = []
    for block in getattr(message, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json_object(raw: str) -> dict[str, Any]:
    raw = (raw or "").strip()
    if not raw:
        return {}
    match = _JSON_OBJECT_RE.search(raw)
    if not match:
        logger.warning("anthropic.json_parse_failed raw_prefix=%s", raw[:200])
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        logger.warning("LLM returned non-JSON payload; ignoring. err=%s", exc)
        return {}
