"""Regression tests for P0-1 Canada-gate removal (TDD: written red, fixed in same branch)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.models import RecordState, Scholarship, StudentProfile
from app.services.recommendations.eligibility import evaluate_match


def _scholarship(**kwargs) -> Scholarship:
    defaults = dict(
        id=uuid.uuid4(),
        title="Test Scholarship",
        provider_name="Test Provider",
        record_state=RecordState.PUBLISHED,
        country_code="GB",
        degree_levels=["MS"],
        citizenship_rules=[],
        min_gpa_value=None,
        field_tags=[],
        source_url="https://example.com",
        summary="",
        deadline_at=None,
        funding_type=None,
        funding_amount_min=None,
        funding_amount_max=None,
        description_embedding=None,
        tier="standard",
    )
    defaults.update(kwargs)
    obj = MagicMock(spec=Scholarship)
    for k, v in defaults.items():
        setattr(obj, k, v)
    obj.record_state = defaults["record_state"]
    return obj


def _profile(**kwargs) -> StudentProfile:
    defaults = dict(
        id=uuid.uuid4(),
        target_country_code="GB",
        citizenship_country_code="PK",
        target_degree_level=MagicMock(value="ms"),
        gpa_value=3.5,
        gpa_scale=4.0,
        target_field="computer science",
        ielts_score=None,
        toefl_score=None,
        gre_score=None,
        gmat_score=None,
        sat_score=None,
    )
    defaults.update(kwargs)
    obj = MagicMock(spec=StudentProfile)
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


def test_uk_target_scholarship_is_not_dropped() -> None:
    """GB profile + published GB scholarship must not be dropped by scope gate."""
    profile = _profile(target_country_code="GB")
    scholarship = _scholarship(country_code="GB")
    result = evaluate_match(profile, scholarship)
    assert result is not None, (
        "GB scholarship should not be dropped for GB-target student after Canada gate removal"
    )


def test_daad_germany_not_name_excluded() -> None:
    """DE profile + published DE DAAD scholarship must not be dropped by name-exclude."""
    profile = _profile(target_country_code="DE")
    scholarship = _scholarship(
        country_code="DE",
        title="DAAD EPOS Scholarships",
        provider_name="DAAD",
    )
    result = evaluate_match(profile, scholarship)
    assert result is not None, (
        "DAAD scholarship should not be excluded after Phase-1 scope gate removal"
    )


def test_non_target_country_still_dropped() -> None:
    """GB profile + published US scholarship must still return None (country_target gate)."""
    profile = _profile(target_country_code="GB")
    scholarship = _scholarship(country_code="US")
    result = evaluate_match(profile, scholarship)
    assert result is None, (
        "US scholarship should still be dropped for GB-target student via country_target rule"
    )
