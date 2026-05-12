"""Unit tests for POST /scholarships/match service logic (Feature 5)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.models import RecordState
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


@pytest.mark.asyncio
async def test_free_user_sees_only_top_three_eligible():
    rows = [
        _scholarship(title="A", deadline_at=_utc_in_days(10), funding_type="full"),
        _scholarship(title="B", deadline_at=_utc_in_days(20), funding_type="full"),
        _scholarship(title="C", deadline_at=_utc_in_days(30), funding_type="full"),
        _scholarship(title="D", deadline_at=_utc_in_days(40), funding_type="full"),
        _scholarship(title="E", deadline_at=_utc_in_days(50), funding_type="full"),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(_user("free"), _student_profile(), ScholarshipMatchRequest())
    assert len(resp.eligible) == 3
    assert resp.visible_limit == 3
    assert len(resp.locked) == 2
    assert resp.upgrade_prompt is not None
    assert "Pro" in resp.upgrade_prompt.message
    assert resp.upgrade_prompt.price.startswith("PKR")


@pytest.mark.asyncio
async def test_pro_user_sees_all_results():
    rows = [
        _scholarship(title="A", deadline_at=_utc_in_days(10), funding_type="full"),
        _scholarship(title="B", deadline_at=_utc_in_days(20), funding_type="full"),
        _scholarship(title="C", deadline_at=_utc_in_days(30), funding_type="full"),
        _scholarship(title="D", deadline_at=_utc_in_days(40), funding_type="full"),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(_user("pro"), _student_profile(), ScholarshipMatchRequest())
    assert len(resp.eligible) == 4
    assert resp.locked == []
    assert resp.upgrade_prompt is None
    assert resp.visible_limit == 4


@pytest.mark.asyncio
async def test_elite_user_gets_priority_alert_flag():
    rows = [
        _scholarship(title="A", deadline_at=_utc_in_days(5)),
        _scholarship(title="B", deadline_at=_utc_in_days(60)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(_user("elite"), _student_profile(), ScholarshipMatchRequest())
    a, b = resp.eligible[0], resp.eligible[1]
    assert a.priority_alert_eligible is True
    assert b.priority_alert_eligible is False


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
    assert resp.total_found == 0


@pytest.mark.asyncio
async def test_cgpa_within_stretch_tolerance_demoted_not_excluded():
    rows = [
        _scholarship(min_gpa_value=3.7, deadline_at=_utc_in_days(30)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(
        _user("pro"),
        _student_profile(gpa_value=3.55),
        ScholarshipMatchRequest(),
    )
    assert len(resp.stretch) == 1
    assert len(resp.eligible) == 0


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
    assert resp.total_found == 0


@pytest.mark.asyncio
async def test_missing_ielts_demoted_to_partial():
    rows = [
        _scholarship(deadline_at=_utc_in_days(30)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(
        _user("pro"),
        _student_profile(ielts_score=None),
        ScholarshipMatchRequest(),
    )
    assert len(resp.partially_eligible) == 1
    assert resp.partially_eligible[0].match_reason


@pytest.mark.asyncio
async def test_nationality_rule_excludes_non_pk_only_record():
    rows = [
        _scholarship(citizenship_rules=["IN"], deadline_at=_utc_in_days(30)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(_user("pro"), _student_profile(), ScholarshipMatchRequest())
    assert resp.total_found == 0


@pytest.mark.asyncio
async def test_open_to_all_nationalities_included():
    rows = [
        _scholarship(citizenship_rules=["*"], deadline_at=_utc_in_days(30)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(_user("pro"), _student_profile(), ScholarshipMatchRequest())
    assert resp.total_found == 1


@pytest.mark.asyncio
async def test_response_includes_fully_funded_count():
    rows = [
        _scholarship(funding_type="full", deadline_at=_utc_in_days(30)),
        _scholarship(funding_type="partial", deadline_at=_utc_in_days(60)),
        _scholarship(funding_type="gta_gra", deadline_at=_utc_in_days(45)),
    ]
    svc = ScholarshipMatchService(_FakeDB(rows))
    resp = await svc.match(_user("pro"), _student_profile(funding_requirement=None), ScholarshipMatchRequest())
    assert resp.fully_funded_count == 2


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
    assert resp.total_found == 1
