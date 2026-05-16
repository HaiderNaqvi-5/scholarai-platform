"""Unit tests for the Elite application strategy report (PRD §0.6).

Covers the Elite gate (402 raised before any DB access) and the pure
Safety/Target/Reach university classifier. Full assembly is exercised
end-to-end in the Phase 8 integration pass.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.schemas.reports import StrategyReportRequest
from app.services.reports.strategy_report import (
    StrategyReportService,
    _classify_university,
)


def _user(plan: str = "elite", currency: str = "PKR"):
    return SimpleNamespace(
        id=uuid.uuid4(), plan=plan, plan_currency=currency, full_name="Zara Khan"
    )


def _uni(min_cgpa):
    return SimpleNamespace(
        id=uuid.uuid4(),
        name="Test University",
        country="GB",
        min_cgpa=min_cgpa,
    )


@pytest.mark.asyncio
async def test_free_user_blocked_before_db_access():
    # db is None — if the gate did not fire first this would AttributeError.
    svc = StrategyReportService(db=None)
    with pytest.raises(HTTPException) as excinfo:
        await svc.generate(_user("free"), StrategyReportRequest())
    assert excinfo.value.status_code == 402
    assert excinfo.value.detail["required_plan"] == ["elite", "institution"]


@pytest.mark.asyncio
async def test_pro_user_blocked_before_db_access():
    svc = StrategyReportService(db=None)
    with pytest.raises(HTTPException) as excinfo:
        await svc.generate(_user("pro"), StrategyReportRequest())
    assert excinfo.value.status_code == 402


def test_classify_university_safety_target_reach():
    # us_gpa 3.8 vs min 3.0 -> margin 0.8 -> Safety
    tier, _ = _classify_university(_uni(3.0), us_gpa=3.8)
    assert tier == "Safety"

    # us_gpa 3.5 vs min 3.5 -> margin 0.0 -> Target
    tier, _ = _classify_university(_uni(3.5), us_gpa=3.5)
    assert tier == "Target"

    # us_gpa 3.0 vs min 3.8 -> margin -0.8 -> Reach
    tier, _ = _classify_university(_uni(3.8), us_gpa=3.0)
    assert tier == "Reach"


def test_classify_university_missing_data_defaults_to_target():
    tier, reason = _classify_university(_uni(None), us_gpa=3.5)
    assert tier == "Target"
    assert "CGPA" in reason

    tier, _ = _classify_university(_uni(3.0), us_gpa=None)
    assert tier == "Target"
