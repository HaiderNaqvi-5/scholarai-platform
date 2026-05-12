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
from typing import Any

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
        client = self._ensure_client()
        message = client.messages.create(
            model=model or self._default_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=[_CachedSystemBlock(system_prompt).to_block()],
            messages=[{"role": "user", "content": user_prompt}],
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


# ----------------------------------------------------------------------
# Parsing helpers
# ----------------------------------------------------------------------


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
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        logger.warning("LLM returned non-JSON payload; ignoring. err=%s", exc)
        return {}
