"""Unit tests for the Elite professor cold-email generator (PRD §0.6)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app.models import DocumentRecord, DocumentType
from app.schemas.professor_email import ProfessorEmailRequest
from app.services.documents.professor_email import (
    ProfessorEmailService,
    _deterministic_email,
)


def _user(plan: str = "elite", currency: str = "PKR"):
    return SimpleNamespace(id=uuid.uuid4(), plan=plan, plan_currency=currency)


def _payload(**overrides) -> ProfessorEmailRequest:
    base = dict(
        professor_name="Dr. Ada Lovelace",
        university="University of Manchester",
        research_area="machine learning systems for low-resource languages",
        student_pitch=(
            "I built an Urdu speech-to-text pipeline as my NUST final-year "
            "project and want to extend it into a PhD on low-resource ASR."
        ),
        position_type="phd",
    )
    base.update(overrides)
    return ProfessorEmailRequest(**base)


class _FakeBurnCapResult:
    """Result stub for the burn-cap pre-flight ``SUM(cost_pkr_micro)`` query.

    ``scalar_one`` returns 0 so ``assert_within_burn_cap`` always passes in
    these unit tests (no prior ledger spend).
    """

    def scalar_one(self) -> int:
        return 0


class _FakeDB:
    def __init__(self) -> None:
        self.added: list[Any] = []
        self.flushed = 0
        self.refreshed: list[Any] = []

    async def execute(self, _stmt):
        # Only the burn-cap aggregate query reaches here in these tests.
        return _FakeBurnCapResult()

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


def test_deterministic_email_has_subject_and_body():
    subject, body = _deterministic_email(_payload())
    assert "Dr. Ada Lovelace" in body
    assert "machine learning systems" in body
    assert "[Your name]" in body
    assert subject  # non-empty
    assert len(body.split()) >= 40


def test_deterministic_email_ra_changes_the_ask():
    _, phd_body = _deterministic_email(_payload(position_type="phd"))
    _, ra_body = _deterministic_email(_payload(position_type="ra"))
    assert "PhD position" in phd_body
    assert "research assistantship" in ra_body


@pytest.mark.asyncio
async def test_free_user_blocked_with_402():
    svc = ProfessorEmailService(_FakeDB())
    with pytest.raises(HTTPException) as excinfo:
        await svc.generate(_user("free"), _payload())
    assert excinfo.value.status_code == 402
    assert excinfo.value.detail["required_plan"] == ["elite", "institution"]


@pytest.mark.asyncio
async def test_pro_user_blocked_with_402():
    svc = ProfessorEmailService(_FakeDB())
    with pytest.raises(HTTPException) as excinfo:
        await svc.generate(_user("pro"), _payload())
    assert excinfo.value.status_code == 402


@pytest.mark.asyncio
async def test_elite_user_gets_email_via_deterministic_fallback():
    db = _FakeDB()
    svc = ProfessorEmailService(db)
    response = await svc.generate(_user("elite"), _payload())
    assert response.document_id is not None
    assert response.used_llm is False
    assert response.model_used == "deterministic_template"
    assert response.email_subject
    assert "[Your name]" in response.email_body
    # Persisted as a DocumentRecord of the new type. (The burn-cap wrapper
    # also writes a synthetic UsageLedger row on the deterministic-template
    # fallback path — Task 11 — so we filter to DocumentRecord here rather
    # than asserting an exact add count.)
    doc_rows = [obj for obj in db.added if isinstance(obj, DocumentRecord)]
    assert len(doc_rows) == 1
    assert doc_rows[0].document_type == DocumentType.PROFESSOR_EMAIL


@pytest.mark.asyncio
async def test_institution_user_also_passes_gate():
    svc = ProfessorEmailService(_FakeDB())
    response = await svc.generate(_user("institution"), _payload())
    assert response.document_id is not None
