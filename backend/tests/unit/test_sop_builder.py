"""Unit tests for the Pakistan-context SOP builder (Feature 7)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException
from sqlalchemy.sql import Select

from app.models import DocumentRecord, DocumentType
from app.schemas.sop import SOPDraftRequest, SOPInputs
from app.services.documents.sop_builder import (
    PARAGRAPH_LABELS,
    SOPBuilderService,
    _build_user_prompt,
    _deterministic_draft,
    _split_paragraphs,
    _word_count,
)


def _inputs(**overrides) -> SOPInputs:
    base = dict(
        academic_background=(
            "I graduated from NUST in 2024 with a CGPA of 3.7 in Computer Science."
        ),
        research_experience=(
            "I worked on a CV pipeline that won the FYP showcase award."
        ),
        professional_experience=(
            "I interned at a Lahore-based fintech building ETL pipelines for 6 months."
        ),
        why_this_program="The program's emphasis on ML systems matches my trajectory.",
        why_this_country="Germany's tuition-free public universities and STEM strength.",
        career_goals=(
            "After my MS I want to lead applied research at a Pakistani EdTech startup."
        ),
        challenges_overcome="Being the first in my family to pursue a research degree.",
        gap_explanation=None,
    )
    base.update(overrides)
    return SOPInputs(**base)


def _user(plan: str = "free", currency: str = "PKR", lifetime_sop_count: int = 0):
    """Build a stub user; the new free-tier gate reads ``lifetime_sop_count`` directly."""
    return SimpleNamespace(
        id=uuid.uuid4(),
        plan=plan,
        plan_currency=currency,
        lifetime_sop_count=lifetime_sop_count,
    )


class _FakeResult:
    """Stub for ``Result`` covering both legacy ``.scalar()`` and the new
    ``.scalar_one_or_none()`` call path used by ``_assert_sop_quota``.
    Also exposes ``.scalar_one()`` so the burn-cap pre-flight query
    (``coalesce(sum(...), 0)``) finds a numeric default when the queue is
    drained.
    """

    def __init__(self, scalar=None):
        self._scalar = scalar

    def scalar(self):
        return self._scalar

    def scalar_one(self):
        # `_assert_within_burn_cap` reads a `SUM(...)` aggregate; the fake
        # DB returns 0 for any drained queue position so spent-to-date is 0
        # and the assertion always passes in unit tests.
        return self._scalar if self._scalar is not None else 0

    def scalar_one_or_none(self):
        return self._scalar


class _FakeDB:
    """Loose ``AsyncSession`` stub.

    SELECT statements return whatever queued ``_FakeResult`` is next (default
    empty). All other statements (UPDATE on ``User`` for free, ``pg_insert``
    on ``SopMonthlyUsage`` for pro/elite) are accepted as no-ops so the
    canonical ``_record_sop_use`` accounting at the tail of ``draft()`` never
    explodes inside the stub.
    """

    def __init__(self, monthly_usage_row: Any = None):
        # _queue is consumed in order by SELECTs; non-SELECT statements skip it.
        self._queue: list[_FakeResult] = [_FakeResult(monthly_usage_row)]
        self.added: list[Any] = []
        self.flushed = 0
        self.refreshed: list[Any] = []
        self.non_select_calls: list[Any] = []

    async def execute(self, statement):
        if isinstance(statement, Select):
            if self._queue:
                return self._queue.pop(0)
            return _FakeResult(None)
        # update / pg_insert / anything else: no-op result.
        self.non_select_calls.append(statement)
        return _FakeResult(None)

    def add(self, obj) -> None:
        self.added.append(obj)
        # mimic DocumentRecord identity
        if isinstance(obj, DocumentRecord):
            if obj.id is None:
                obj.id = uuid.uuid4()
            obj.created_at = datetime.now(timezone.utc)

    async def flush(self) -> None:
        self.flushed += 1

    async def refresh(self, obj) -> None:
        self.refreshed.append(obj)

    async def get(self, _model, _pk):
        return None


def _payload() -> SOPDraftRequest:
    return SOPDraftRequest(program_name="MS Computer Science", sop_inputs=_inputs())


@pytest.mark.asyncio
async def test_deterministic_draft_produces_six_paragraphs_and_target_length():
    payload = _payload()
    text = _deterministic_draft(payload, ctx=None)
    paragraphs = _split_paragraphs(text)
    assert len(paragraphs) == 6
    assert 200 <= _word_count(text) <= 1200  # comfortably in SOP territory for a template


def test_user_prompt_contains_program_and_inputs():
    payload = _payload()
    prompt = _build_user_prompt(payload, None)
    assert "MS Computer Science" in prompt
    assert "NUST" in prompt


@pytest.mark.asyncio
async def test_free_user_blocked_after_one_sop():
    # Free gate now reads ``user.lifetime_sop_count`` directly (no DB call).
    db = _FakeDB()
    svc = SOPBuilderService(db)
    with pytest.raises(HTTPException) as excinfo:
        await svc.draft(_user("free", lifetime_sop_count=1), _payload())
    err = excinfo.value
    assert err.status_code == 402
    # New error envelope from ``raise_plan_required``.
    assert err.detail["error"] == "plan_required"
    assert "pro" in err.detail["required_plan"]
    assert err.detail["current_plan"] == "free"


@pytest.mark.asyncio
async def test_free_user_allowed_first_sop():
    db = _FakeDB()
    svc = SOPBuilderService(db)
    response = await svc.draft(_user("free", lifetime_sop_count=0), _payload())
    assert response.document_id is not None
    assert response.used_llm is False  # no API key in tests
    assert response.model_used == "deterministic_template"
    assert response.paragraph_labels == PARAGRAPH_LABELS
    assert response.line_feedback is None


@pytest.mark.asyncio
async def test_elite_user_gets_line_feedback_via_deterministic_fallback():
    # No existing monthly-usage row -> Elite is well under the 10/month cap.
    db = _FakeDB(monthly_usage_row=None)
    svc = SOPBuilderService(db)
    response = await svc.draft(_user("elite"), _payload())
    assert response.line_feedback is not None
    assert len(response.line_feedback) == 6
    assert response.line_feedback[0].paragraph_label == PARAGRAPH_LABELS[0]


@pytest.mark.asyncio
async def test_pro_user_first_sop_succeeds_without_quota_row():
    """A Pro user with no monthly-usage row yet is well under the 5/month cap."""
    db = _FakeDB(monthly_usage_row=None)
    svc = SOPBuilderService(db)
    response = await svc.draft(_user("pro"), _payload())
    assert response.document_id is not None


@pytest.mark.asyncio
async def test_pro_user_at_cap_returns_429():
    """Pro user already at 5/month -> HTTP 429 ``sop_quota_exhausted``."""
    # Simulate a SopMonthlyUsage row exposing ``sop_count`` at the Pro cap.
    used_row = SimpleNamespace(sop_count=5)
    db = _FakeDB(monthly_usage_row=used_row)
    svc = SOPBuilderService(db)
    with pytest.raises(HTTPException) as excinfo:
        await svc.draft(_user("pro"), _payload())
    err = excinfo.value
    assert err.status_code == 429
    assert err.detail["error"] == "sop_quota_exhausted"
    assert err.detail["cap"] == 5
    assert err.detail["upgrade_url"] == "/upgrade"


def test_grounded_context_carries_limitations_disclaimer():
    payload = _payload()
    text = _deterministic_draft(payload, ctx={"facts": ["Target: Chevening."]})
    assert "validated scholarship context" in text.lower()
