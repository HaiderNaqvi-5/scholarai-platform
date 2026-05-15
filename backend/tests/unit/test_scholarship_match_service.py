"""Unit tests for POST /scholarships/match service logic (Feature 5).

Q1 retier (Task 7) — the public surface is neutral. These tests assert
the new ``MatchResponse`` shape (items + unlock_offer) and the per-plan
policy (free=stretch-only, pro=blur top 3 eligible, elite=full reveal).
No internal vocabulary (eligible/partial/stretch/premium/standard/
bucket/tier) may appear in the serialised response.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.models import RecordState, ScholarshipTier
from app.schemas.scholarships_match import ScholarshipMatchRequest
from app.services.scholarships.match_service import ScholarshipMatchService


def _utc_in_days(days: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=days)


def _scholarship(**overrides):
    base = dict(
        id=uuid.uuid4(),
        title="Test Scholarship",
        provider_name="Provider",
        country_code="GB",
        deadline_at=_utc_in_days(60),
        funding_type="full",
        funding_amount_min=20000,
        funding_amount_max=30000,
        field_tags=["cs", "ds_ai"],
        degree_levels=["MS"],
        citizenship_rules=["PK"],
        min_gpa_value=3.0,
        record_state=RecordState.PUBLISHED,
        provenance_payload={"tags": []},
        tier=ScholarshipTier.STANDARD,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _student_profile(**overrides):
    base = dict(
        gpa_value=3.6,
        target_degree_level=SimpleNamespace(value="MS"),
        target_countries=["GB", "DE"],
        target_country_code="GB",
        target_fields=["cs", "ds_ai"],
        target_field="cs",
        ielts_score=7.0,
        gre_quant=None,
        gre_verbal=None,
        funding_requirement="fully_funded_only",
        citizenship_country_code="PK",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _user(plan: str = "free", currency: str = "PKR"):
    return SimpleNamespace(plan=plan, plan_currency=currency)


class _FakeDB:
    def __init__(self, rows):
        self._rows = rows

    async def execute(self, _stmt):
        rows = self._rows

        class _ScalarResult:
            def all(self_inner):
                return rows

        class _Result:
            def scalars(self_inner):
                return _ScalarResult()

        return _Result()


# ----------------------------------------------------------------------
# Q1 retier (Task 7) — per-plan policy on the neutral public response.
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_free_returns_3_or_fewer_unlocked():
    """Free tier: only neutral, unlocked rows, capped at MATCH_CAP['free']=3."""
    # Mix of eligible (will be hidden from free) plus stretch-class rows
    # (CGPA between min-tolerance and min — these are what free sees).
    rows = [
        _scholarship(title="Stretch A", min_gpa_value=3.7, deadline_at=_utc_in_days(20)),
        _scholarship(title="Stretch B", min_gpa_value=3.7, deadline_at=_utc_in_days(30)),
        _scholarship(title="Stretch C", min_gpa_value=3.7, deadline_at=_utc_in_days(40)),
        _scholarship(title="Stretch D", min_gpa_value=3.7, deadline_at=_utc_in_days(50)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(_user("free"), _student_profile(gpa_value=3.55), ScholarshipMatchRequest())
    assert len(resp.items) <= 3
    assert all(row.locked is False for row in resp.items)


@pytest.mark.asyncio
async def test_free_unlock_offer_points_to_pro():
    """Free with extra hidden rows surfaces an UnlockOffer toward Pro."""
    rows = [
        _scholarship(title="A", deadline_at=_utc_in_days(10)),
        _scholarship(title="B", deadline_at=_utc_in_days(20)),
        _scholarship(title="C", deadline_at=_utc_in_days(30)),
        _scholarship(title="D", deadline_at=_utc_in_days(40)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(_user("free"), _student_profile(), ScholarshipMatchRequest())
    # Free has hidden rows here (these classify as eligible — free never
    # shows them), so the unlock offer is present and aimed at Pro.
    assert resp.unlock_offer is not None
    assert resp.unlock_offer.to_plan == "pro"
    assert resp.unlock_offer.locked_count >= 1


@pytest.mark.asyncio
async def test_pro_full_pool_top_eligible_blurred():
    """Pro: pool up to 6 rows, first 3 eligible rows render as locked
    placeholders with neutral copy."""
    # Six eligible rows — first three render locked, remaining three
    # unlocked, capped at MATCH_CAP['pro']=6.
    rows = [
        _scholarship(title="E1", deadline_at=_utc_in_days(10)),
        _scholarship(title="E2", deadline_at=_utc_in_days(20)),
        _scholarship(title="E3", deadline_at=_utc_in_days(30)),
        _scholarship(title="E4", deadline_at=_utc_in_days(40)),
        _scholarship(title="E5", deadline_at=_utc_in_days(50)),
        _scholarship(title="E6", deadline_at=_utc_in_days(60)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(_user("pro"), _student_profile(), ScholarshipMatchRequest())
    assert len(resp.items) <= 6
    locked_rows = [r for r in resp.items if r.locked]
    assert 1 <= len(locked_rows) <= 3
    for row in locked_rows:
        assert row.id is None
        assert row.name == "Reveal with upgrade"
        assert row.provider == "Reveal with upgrade"
        assert row.deadline is None
        assert row.funding_amount is None
        assert isinstance(row.compatibility, float)
        assert 0.0 <= row.compatibility <= 1.0


@pytest.mark.asyncio
async def test_pro_unlock_offer_points_to_elite_when_any_blurred():
    """Pro with at least one eligible row gets an UnlockOffer to Elite."""
    rows = [
        _scholarship(title="A", deadline_at=_utc_in_days(10)),
        _scholarship(title="B", deadline_at=_utc_in_days(30)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(_user("pro"), _student_profile(), ScholarshipMatchRequest())
    assert resp.unlock_offer is not None
    assert resp.unlock_offer.to_plan == "elite"
    assert resp.unlock_offer.locked_count >= 1


@pytest.mark.asyncio
async def test_pro_no_unlock_offer_when_no_eligible_matches():
    """Pro with zero eligible rows in the pool: no blur, no UnlockOffer."""
    # Single row that classifies as stretch (CGPA in tolerance band).
    rows = [
        _scholarship(title="Stretch", min_gpa_value=3.7, deadline_at=_utc_in_days(30)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(
        _user("pro"),
        _student_profile(gpa_value=3.55),
        ScholarshipMatchRequest(),
    )
    assert all(row.locked is False for row in resp.items)
    assert resp.unlock_offer is None


@pytest.mark.asyncio
async def test_elite_full_reveal():
    """Elite: every row is unlocked, no UnlockOffer."""
    rows = [
        _scholarship(title="A", deadline_at=_utc_in_days(10)),
        _scholarship(title="B", deadline_at=_utc_in_days(60)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(_user("elite"), _student_profile(), ScholarshipMatchRequest())
    assert all(row.locked is False for row in resp.items)
    assert resp.unlock_offer is None


@pytest.mark.asyncio
async def test_response_contains_no_internal_vocab():
    """CI vocab guard pre-check: serialised response carries no internal
    bucket / tier vocabulary (eligible / partial / stretch / premium /
    standard / bucket / tier)."""
    rows = [
        _scholarship(title="A", deadline_at=_utc_in_days(10)),
        _scholarship(title="B", min_gpa_value=3.7, deadline_at=_utc_in_days(20)),
        _scholarship(title="C", deadline_at=_utc_in_days(30)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(_user("pro"), _student_profile(gpa_value=3.55), ScholarshipMatchRequest())
    payload = json.dumps(resp.model_dump(mode="json"))
    banned = re.compile(r"eligible|partial|stretch|premium|standard|bucket|tier", re.IGNORECASE)
    assert not banned.search(payload), f"internal vocabulary leaked: {payload}"


# ----------------------------------------------------------------------
# Pre-existing classification + filter tests — updated to the neutral
# public shape (assertions touching old bucket fields rewritten only).
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_country_filter_excludes_non_targeted():
    rows = [
        _scholarship(country_code="US", deadline_at=_utc_in_days(30)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(
        _user("pro"),
        _student_profile(target_countries=["GB"], target_country_code="GB"),
        ScholarshipMatchRequest(),
    )
    assert resp.items == []


@pytest.mark.asyncio
async def test_cgpa_within_stretch_tolerance_demoted_not_excluded():
    """A row that classifies as stretch is still returned on the Pro
    pool (unlocked — blur only fires on the eligible bucket)."""
    rows = [
        _scholarship(min_gpa_value=3.7, deadline_at=_utc_in_days(30)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(
        _user("pro"),
        _student_profile(gpa_value=3.55),
        ScholarshipMatchRequest(),
    )
    assert len(resp.items) == 1
    assert resp.items[0].locked is False


@pytest.mark.asyncio
async def test_cgpa_far_below_excluded():
    rows = [
        _scholarship(min_gpa_value=3.7, deadline_at=_utc_in_days(30)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(
        _user("pro"),
        _student_profile(gpa_value=3.0),
        ScholarshipMatchRequest(),
    )
    assert resp.items == []


@pytest.mark.asyncio
async def test_missing_ielts_demoted_to_partial():
    """A row demoted to the partial bucket internally still surfaces on
    the Pro pool — unlocked, because blur targets eligible-bucket rows."""
    rows = [
        _scholarship(deadline_at=_utc_in_days(30)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(
        _user("pro"),
        _student_profile(ielts_score=None),
        ScholarshipMatchRequest(),
    )
    assert len(resp.items) == 1
    assert resp.items[0].locked is False


@pytest.mark.asyncio
async def test_nationality_rule_excludes_non_pk_only_record():
    rows = [
        _scholarship(citizenship_rules=["IN"], deadline_at=_utc_in_days(30)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(_user("pro"), _student_profile(), ScholarshipMatchRequest())
    assert resp.items == []


@pytest.mark.asyncio
async def test_open_to_all_nationalities_included():
    rows = [
        _scholarship(citizenship_rules=["*"], deadline_at=_utc_in_days(30)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(_user("pro"), _student_profile(), ScholarshipMatchRequest())
    assert len(resp.items) == 1


@pytest.mark.asyncio
async def test_request_body_overrides_profile_countries():
    rows = [
        _scholarship(country_code="DE", deadline_at=_utc_in_days(30)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(
        _user("pro"),
        _student_profile(target_countries=["GB"], target_country_code="GB"),
        ScholarshipMatchRequest(countries=["DE"]),
    )
    assert len(resp.items) == 1
