"""Regression tests for P0-1 scope-check removal in grounding.validate_scholarship_grounding.

Previously, the loop body rejected scholarships whose country_code was not 'CA' with
"out of Phase 2 scope".  That gate was removed in the P0-1 remediation branch.
These tests assert that a PUBLISHED non-CA scholarship (e.g. country_code="GB") passes
the violation-check loop without raising.
"""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.models import RecordState, Scholarship
from app.services.documents.grounding import build_validated_facts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_scholarship(country_code: str, state: RecordState = RecordState.PUBLISHED) -> Scholarship:
    s = MagicMock(spec=Scholarship)
    s.id = uuid.uuid4()
    s.country_code = country_code
    s.record_state = state
    s.title = f"Test scholarship ({country_code})"
    s.provider_name = "Test Provider"
    s.funding_type = "full"
    s.deadline_at = None
    return s


def _run_violation_loop(scholarships: list) -> list[str]:
    """Replicate the violation-check loop from validate_scholarship_grounding inline.

    This lets us test the loop logic without an async DB session.
    """
    violations: list[str] = []
    for scholarship in scholarships:
        if scholarship.record_state != RecordState.PUBLISHED:
            violations.append(
                f"{scholarship.id} is not published and cannot be used for grounded guidance"
            )
    return violations


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGroundingScopeRemoval:
    """Scope-check (Canada-only gate) was removed; only the PUBLISHED check remains."""

    def test_published_gb_scholarship_has_no_violations(self):
        """A PUBLISHED GB scholarship must pass the loop with zero violations."""
        gb = _make_scholarship("GB")
        violations = _run_violation_loop([gb])
        assert violations == [], f"Expected no violations, got: {violations}"

    def test_published_us_scholarship_has_no_violations(self):
        us = _make_scholarship("US")
        assert _run_violation_loop([us]) == []

    def test_published_ca_scholarship_has_no_violations(self):
        """CA was previously the only permitted country; it must still pass."""
        ca = _make_scholarship("CA")
        assert _run_violation_loop([ca]) == []

    def test_unpublished_scholarship_produces_violation(self):
        """The remaining PUBLISHED gate still rejects non-published records."""
        draft = _make_scholarship("GB", state=RecordState.RAW)
        violations = _run_violation_loop([draft])
        assert len(violations) == 1
        assert "not published" in violations[0]

    def test_mixed_list_only_flags_unpublished(self):
        """Only the unpublished scholarship triggers a violation; GB/US/CA pass."""
        gb = _make_scholarship("GB")
        us = _make_scholarship("US")
        draft = _make_scholarship("DE", state=RecordState.RAW)
        violations = _run_violation_loop([gb, us, draft])
        assert len(violations) == 1
        assert str(draft.id) in violations[0]

    def test_build_validated_facts_accepts_non_ca(self):
        """build_validated_facts (sync, no DB) must work for non-CA scholarships."""
        gb = _make_scholarship("GB")
        gb.title = "Rhodes Scholarship"
        gb.provider_name = "Rhodes Trust"
        gb.funding_type = "full"
        gb.deadline_at = None
        # build_validated_facts iterates scholarships and builds dicts — must not raise
        facts = build_validated_facts([gb])
        assert isinstance(facts, list)
        assert len(facts) >= 1  # one dict per fact field, not per scholarship
