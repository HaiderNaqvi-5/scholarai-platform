"""Unit tests for privacy / consent / B2B (Feature 9.5)."""

from __future__ import annotations

import hashlib
import uuid
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app.demo.legal_documents import LEGAL_DOCUMENTS_V1
from app.services.privacy.b2b_share import B2BShareService, _redact_email
from app.services.privacy.lead_score import compute_lead_score


# ---------------------------------------------------------------------
# Lead score
# ---------------------------------------------------------------------


def _profile(**overrides) -> SimpleNamespace:
    base = dict(
        gpa_value=3.7,
        ielts_score=7.0,
        toefl_score=None,
        funding_requirement="fully_funded_only",
        pakistani_university="NUST",
        degree_subject="Computer Science",
        graduation_year=2024,
        city_of_origin="Islamabad",
        linkedin_url="https://linkedin.com/in/zara",
        github_url=None,
        research_publication_count=1,
        years_work_experience=2,
        target_fields=["cs", "ds_ai"],
        target_countries=["GB", "DE"],
        # Fields used by B2B snapshot
        citizenship_country_code="PK",
        target_degree_level=SimpleNamespace(value="MS"),
        lead_score=85,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_lead_score_high_for_complete_strong_profile() -> None:
    score = compute_lead_score(_profile())
    assert 80 <= score <= 100


def test_lead_score_low_for_empty_profile() -> None:
    empty = SimpleNamespace(
        gpa_value=None,
        ielts_score=None,
        toefl_score=None,
        funding_requirement=None,
        pakistani_university=None,
        degree_subject=None,
        graduation_year=None,
        city_of_origin=None,
        linkedin_url=None,
        github_url=None,
        research_publication_count=None,
        years_work_experience=None,
        target_fields=[],
        target_countries=[],
    )
    assert compute_lead_score(empty) == 0


def test_lead_score_clamped_between_0_and_100() -> None:
    score = compute_lead_score(_profile(target_fields=["a"] * 30, target_countries=["a"] * 30))
    assert 0 <= score <= 100


# ---------------------------------------------------------------------
# B2B share gate
# ---------------------------------------------------------------------


class _FakeResult:
    def __init__(self, scalar=None):
        self._scalar = scalar

    def scalar_one_or_none(self):
        return self._scalar


class _FakeDB:
    def __init__(self, *, institution=None, profile=None, consent_row=None):
        self._institution = institution
        self._profile = profile
        self._consent_row = consent_row
        self.added: list[Any] = []
        self.flushed = 0
        self.refreshed: list[Any] = []

    async def execute(self, _statement):
        # All execute() calls return the cached consent row look-up or profile.
        return _FakeResult(self._consent_row if "consent" in str(_statement).lower() else self._profile)

    async def get(self, _model, _pk):
        return self._institution

    def add(self, obj) -> None:
        if not hasattr(obj, "id") or obj.id is None:
            obj.id = uuid.uuid4()
        if not hasattr(obj, "shared_at") or obj.shared_at is None:
            obj.shared_at = datetime.now(timezone.utc)
        self.added.append(obj)

    async def flush(self) -> None:
        self.flushed += 1

    async def refresh(self, obj) -> None:
        self.refreshed.append(obj)


def _user_with_consent(consent: bool = True):
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="zara@example.com",
        plan="elite",
        billing_country="PK",
        b2b_share_consent=consent,
    )


@pytest.mark.asyncio
async def test_b2b_share_rejected_without_consent():
    user = _user_with_consent(consent=False)
    svc = B2BShareService(_FakeDB())
    with pytest.raises(HTTPException) as excinfo:
        await svc.share_profile(
            target_user=user,
            university_id=uuid.uuid4(),
            share_reason="match",
            shared_with_email=None,
        )
    err = excinfo.value
    assert err.status_code == 403
    assert err.detail["error"] == "b2b_share_consent_missing"


@pytest.mark.asyncio
async def test_b2b_share_rejected_when_institution_dpa_missing():
    institution = SimpleNamespace(dpa_signed_at=None)
    svc = B2BShareService(_FakeDB(institution=institution))
    with pytest.raises(HTTPException) as excinfo:
        await svc.share_profile(
            target_user=_user_with_consent(True),
            university_id=uuid.uuid4(),
            institution_id=uuid.uuid4(),
            share_reason="match",
            shared_with_email=None,
        )
    err = excinfo.value
    assert err.status_code == 403
    assert err.detail["error"] == "institution_dpa_missing"


@pytest.mark.asyncio
async def test_b2b_share_persists_lead_with_snapshot():
    institution = SimpleNamespace(dpa_signed_at=datetime.now(timezone.utc))
    profile = _profile()
    consent_row = SimpleNamespace(id=uuid.uuid4())
    db = _FakeDB(institution=institution, profile=profile, consent_row=consent_row)
    svc = B2BShareService(db)
    lead = await svc.share_profile(
        target_user=_user_with_consent(True),
        university_id=uuid.uuid4(),
        institution_id=uuid.uuid4(),
        share_reason="match",
        shared_with_email="recruit@nust.edu.pk",
    )
    assert lead.id is not None
    assert lead.profile_snapshot
    assert lead.consent_audit_log_id == consent_row.id


def test_b2b_share_invalid_reason_rejected():
    svc = B2BShareService(_FakeDB(institution=SimpleNamespace(dpa_signed_at=None)))
    import asyncio

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            svc.share_profile(
                target_user=_user_with_consent(True),
                university_id=uuid.uuid4(),
                share_reason="cold_call",
                shared_with_email=None,
            )
        )
    assert excinfo.value.status_code == 400


def test_redact_email_keeps_domain_drops_local():
    assert _redact_email("zara@example.com") == "z***a@example.com"
    assert _redact_email("zi@example.com") == "z@example.com"
    assert _redact_email(None) is None
    assert _redact_email("no-at-symbol") is None


# ---------------------------------------------------------------------
# Legal documents seed
# ---------------------------------------------------------------------


def test_seed_includes_all_required_legal_docs():
    slugs = {doc["slug"] for doc in LEGAL_DOCUMENTS_V1}
    assert slugs == {"terms", "privacy", "cookies", "b2b_data_use", "aup"}


def test_seed_contains_liability_cap_and_no_guarantee_wording():
    terms = next(doc for doc in LEGAL_DOCUMENTS_V1 if doc["slug"] == "terms")
    body = terms["body_markdown"].lower()
    assert "no guarantee" in body
    assert "pkr 1,000" in body
    assert "arbitration" in body
    assert "class" in body and "waiver" in body


def test_privacy_doc_documents_consent_revocation_and_export_routes():
    privacy = next(doc for doc in LEGAL_DOCUMENTS_V1 if doc["slug"] == "privacy")
    body = privacy["body_markdown"]
    assert "POST /api/v1/privacy/data-export" in body
    assert "POST /api/v1/privacy/account-deletion" in body
    assert "30 days" in body


def test_b2b_doc_requires_dpa_before_data_share():
    b2b = next(doc for doc in LEGAL_DOCUMENTS_V1 if doc["slug"] == "b2b_data_use")
    assert "dpa" in b2b["body_markdown"].lower()
    assert "snapshot" in b2b["body_markdown"].lower()


def test_legal_doc_sha256_can_be_computed_for_each():
    for doc in LEGAL_DOCUMENTS_V1:
        digest = hashlib.sha256(doc["body_markdown"].encode("utf-8")).hexdigest()
        assert len(digest) == 64


# ---------------------------------------------------------------------
# Deletion service window
# ---------------------------------------------------------------------


def test_deletion_window_is_thirty_days():
    from app.services.privacy.deletion_service import DELETION_WINDOW

    assert DELETION_WINDOW == timedelta(days=30)
