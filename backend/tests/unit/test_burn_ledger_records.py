"""Burn-cap ledger receives a row after an LLM call (Task 11).

Exercises the ``complete_with_accounting`` wrapper end-to-end via the
SOP builder, which is the most realistic caller. Two scenarios are
covered:

1. **Deterministic-template path** (no ``ANTHROPIC_API_KEY``): the
   wrapper raises ``LLMUnavailableError`` after writing a synthetic
   zero-cost ledger row that pins the input-token estimate. The SOP
   builder then falls back to its hand-written template.
2. **Live-SDK path** (monkeypatched ``_raw_call``): the wrapper records
   the real usage tokens (``input_tokens=100, output_tokens=50``) and
   the ledger row picks up the correctly priced ``cost_pkr_micro``.

The minimum guarantee asserted by both scenarios: after the LLM call,
``SELECT * FROM usage_ledger WHERE user_id = :user`` returns ≥ 1 row with
``kind`` in ``{"llm_haiku","llm_sonnet"}`` and ``cost_pkr_micro >= 0``
(``>0`` whenever the real-SDK path runs).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy.sql import Select

from app.models import DocumentRecord, UsageLedger
from app.schemas.sop import SOPDraftRequest, SOPInputs
from app.services.documents.sop_builder import SOPBuilderService


# ---------------------------------------------------------------------------
# Test fixtures / fakes
# ---------------------------------------------------------------------------


class _BurnCapResult:
    """Stub for the burn-cap aggregate query result.

    The pre-flight check selects ``SUM(cost_pkr_micro)`` filtered by
    user_id + period; this fake always reports 0 spent so the assertion
    never trips inside unit tests.
    """

    def scalar_one(self) -> int:
        return 0


class _QuotaResult:
    """Stub for the SOP-quota lookup (only used on pro/elite paths)."""

    def scalar_one_or_none(self) -> Any:
        return None


class _FakeDB:
    """In-memory async DB stub.

    Captures every ``db.add(...)`` call so tests can inspect the rows
    that would have hit ``usage_ledger`` / ``document_records``. Routes
    SELECT statements to canned results in the order the SOP builder
    issues them:

    1. quota lookup (SopMonthlyUsage) -> ``_QuotaResult``
    2. burn-cap aggregate (UsageLedger SUM) -> ``_BurnCapResult``
    3. (Elite only) second burn-cap aggregate for line feedback -> ``_BurnCapResult``

    The free-tier path skips (1) because the gate reads
    ``user.lifetime_sop_count`` directly.
    """

    def __init__(self, plan: str = "free") -> None:
        self.added: list[Any] = []
        self.flushed = 0
        self.refreshed: list[Any] = []
        # Free path -> burn-cap only. Pro/Elite path -> quota then burn-cap.
        if plan == "free":
            self._queue: list[Any] = [_BurnCapResult()]
        else:
            self._queue = [_QuotaResult(), _BurnCapResult(), _BurnCapResult()]

    async def execute(self, statement):
        if isinstance(statement, Select):
            if self._queue:
                return self._queue.pop(0)
            return _BurnCapResult()
        # update / pg_insert — accept and return a benign result.
        return _BurnCapResult()

    def add(self, obj) -> None:
        self.added.append(obj)
        if isinstance(obj, DocumentRecord):
            if obj.id is None:
                obj.id = uuid.uuid4()
            obj.created_at = datetime.now(timezone.utc)

    async def flush(self) -> None:
        self.flushed += 1

    async def refresh(self, obj) -> None:
        self.refreshed.append(obj)

    async def get(self, _model, _pk):  # pragma: no cover - not exercised here
        return None

    # --------------------------------------------------------------
    # Test helpers
    # --------------------------------------------------------------

    def ledger_rows(self) -> list[UsageLedger]:
        return [obj for obj in self.added if isinstance(obj, UsageLedger)]


def _user(plan: str = "free", lifetime_sop_count: int = 0):
    """Stub User row that the burn-cap / quota helpers can read from."""
    return SimpleNamespace(
        id=uuid.uuid4(),
        plan=plan,
        plan_currency="PKR",
        lifetime_sop_count=lifetime_sop_count,
    )


def _payload() -> SOPDraftRequest:
    inputs = SOPInputs(
        academic_background=(
            "I graduated from NUST in 2024 with a CGPA of 3.7 in Computer Science."
        ),
        research_experience=(
            "I worked on a computer-vision pipeline that won the FYP showcase."
        ),
        professional_experience=(
            "Six-month internship at a Lahore-based fintech building ETL services."
        ),
        why_this_program="The program's ML systems emphasis matches my trajectory.",
        why_this_country="Germany's tuition-free STEM universities.",
        career_goals=(
            "After my MS I want to lead applied research at a Pakistani EdTech."
        ),
        challenges_overcome="Being the first in my family to pursue a research degree.",
        gap_explanation=None,
    )
    return SOPDraftRequest(program_name="MS Computer Science", sop_inputs=inputs)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_burn_ledger_records_after_sop_draft_offline_fallback() -> None:
    """No API key configured -> deterministic template path.

    ``complete_with_accounting`` still writes a synthetic ledger row
    that pins the input-token estimate so the burn-cap audit trail
    remains complete in offline / CI runs.
    """
    db = _FakeDB(plan="free")
    user = _user("free", lifetime_sop_count=0)

    svc = SOPBuilderService(db)
    # In CI ``ANTHROPIC_API_KEY`` is unset; force-clear just in case so the
    # test exercises the deterministic-template path deterministically.
    svc.llm._api_key = None  # noqa: SLF001 - test seam

    response = await svc.draft(user, _payload())

    # Sanity: deterministic-template draft was returned, not a Claude call.
    assert response.used_llm is False
    assert response.model_used == "deterministic_template"

    rows = db.ledger_rows()
    assert len(rows) >= 1, "expected at least one usage_ledger row from the wrapper"
    row = rows[0]
    assert row.kind in {"llm_haiku", "llm_sonnet"}
    # The synthetic row uses the input-token estimate; output_tokens stays
    # 0 because nothing was actually generated by the SDK.
    assert row.input_tokens >= 1
    assert row.output_tokens == 0
    assert row.endpoint == "documents.sop.draft"
    # cost_pkr_micro is computed from the input-token estimate, which is
    # bounded below by ``max(1, len(blob) // 4)`` -> at minimum a handful
    # of micro-PKR for any non-trivial prompt.
    assert row.cost_pkr_micro >= 0


@pytest.mark.asyncio
async def test_burn_ledger_records_after_sop_draft_with_real_usage(monkeypatch) -> None:
    """API-key-available path -> wrapper records the real usage tokens.

    Monkeypatches ``AnthropicClient._raw_call`` to return a stub message
    with ``usage.input_tokens=100`` and ``usage.output_tokens=50``, so
    the wrapper exercises the accounting path without an external network
    call. The resulting ``cost_pkr_micro`` is then strictly > 0.
    """
    db = _FakeDB(plan="free")
    user = _user("free", lifetime_sop_count=0)

    svc = SOPBuilderService(db)
    # Pretend the SDK is configured. ``_raw_call`` is the only SDK seam
    # so flipping ``_api_key`` + monkeypatching ``_raw_call`` is enough.
    svc.llm._api_key = "test-key"  # noqa: SLF001 - test seam

    class _StubBlock:
        text = (
            "Pakistan has long been under-represented in research circles. "
            "I trained at NUST under faculty who pushed me to translate "
            "every coursework concept into a working artifact. "
            # Each word is one token here; the SOP builder requires >=300
            # words before it accepts a Claude draft as the real thing.
            + " ".join(f"word{n}" for n in range(400))
        )

    stub_message = SimpleNamespace(
        content=[_StubBlock()],
        usage=SimpleNamespace(input_tokens=100, output_tokens=50),
    )

    def _fake_raw_call(self, **_kwargs):  # noqa: ANN001 - matches method shape
        return stub_message

    # Bind as a method so ``self`` is passed correctly.
    monkeypatch.setattr(
        type(svc.llm),
        "_raw_call",
        _fake_raw_call,
        raising=True,
    )

    response = await svc.draft(user, _payload())

    # The SDK stub returned a long-enough draft, so the wrapper returned
    # text and the builder accepted it as a real LLM draft.
    assert response.used_llm is True

    rows = db.ledger_rows()
    assert len(rows) >= 1
    row = rows[0]
    assert row.kind in {"llm_haiku", "llm_sonnet"}
    assert row.input_tokens == 100
    assert row.output_tokens == 50
    assert row.cost_pkr_micro > 0
    assert row.endpoint == "documents.sop.draft"
