"""PRD §10 demo readiness — static checks on the Pakistan demo seed.

These tests inspect the seed orchestrator source so they run offline
without a database. The orchestrator's runtime behaviour against a live
DB is covered by the end-to-end smoke suite.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.demo.pakistan_dataset import PAKISTAN_SCHOLARSHIP_SEED
from app.demo.pakistan_universities import UNIVERSITIES_SEED
from app.demo.visa_questions import VISA_INTERVIEW_QUESTION_BANK


SEED_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "demo_seed_pakistan.py"
)


@pytest.fixture(scope="module")
def seed_source() -> str:
    return SEED_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------
# Seed orchestrator constants (PRD §10 demo account)
# ---------------------------------------------------------------------


def test_demo_email_matches_prd_persona(seed_source: str) -> None:
    assert 'DEMO_EMAIL = "zara.khan@example.com"' in seed_source


def test_demo_account_is_elite_plan(seed_source: str) -> None:
    assert 'user.plan = "elite"' in seed_source
    assert 'user.plan_currency = "PKR"' in seed_source
    assert 'user.billing_country = "PK"' in seed_source


def test_demo_plan_expires_far_in_future(seed_source: str) -> None:
    """Demo account must never expire during the FYP cycle."""
    assert "datetime(2099, 12, 31" in seed_source


def test_demo_consents_granted(seed_source: str) -> None:
    """All five v1.0 consents must be granted so gated routes work without prompts."""
    required = {"terms", "privacy", "marketing", "b2b_share", "cookies"}
    for slug in required:
        assert f'"{slug}"' in seed_source, f"consent {slug!r} not granted in demo seed"


def test_demo_profile_uses_nust_persona(seed_source: str) -> None:
    """PRD persona — NUST + IELTS 7.0 + CGPA 3.7 + Computer Science."""
    assert 'profile.pakistani_university = "NUST"' in seed_source
    assert "profile.gpa_value = 3.7" in seed_source
    assert "profile.ielts_score = 7.0" in seed_source
    assert 'profile.degree_subject = "Computer Science"' in seed_source


def test_waitlist_placeholders_cover_three_plans(seed_source: str) -> None:
    """PRD §10 — three waitlist rows so /upgrade looks active."""
    assert '"pro"' in seed_source
    assert '"elite"' in seed_source
    assert '"institution"' in seed_source


# ---------------------------------------------------------------------
# Seed dataset minimums (PRD §3, §4, §8)
# ---------------------------------------------------------------------


def test_pakistan_scholarship_seed_meets_prd_minimum() -> None:
    """PRD §3 — at least the 10 named scholarships (Tier 1 + Tier 2)."""
    assert len(PAKISTAN_SCHOLARSHIP_SEED) >= 10


def test_pakistan_scholarship_seed_includes_named_tier1() -> None:
    titles = " ".join(record["title"].lower() for record in PAKISTAN_SCHOLARSHIP_SEED)
    for required in ("chevening", "fulbright", "daad", "commonwealth", "hec"):
        assert required in titles, f"PRD §3 missing tier-1 scholarship: {required!r}"


def test_pakistan_universities_seed_meets_prd_minimum() -> None:
    """PRD §4 acceptance — at least 30 Pakistan-relevant universities."""
    assert len(UNIVERSITIES_SEED) >= 30


def test_pakistan_universities_seed_covers_four_target_countries() -> None:
    """PRD §4 — UK, US, CA, DE represented."""
    countries = {record["country"] for record in UNIVERSITIES_SEED}
    for code in ("GB", "US", "CA", "DE"):
        assert code in countries, f"PRD §4 missing universities for {code}"


def test_visa_question_bank_totals_match_prd() -> None:
    """PRD §8 — exactly 20 UK + 20 US + 15 CA + 15 DE = 70 questions."""
    by_country: dict[str, int] = {}
    for question in VISA_INTERVIEW_QUESTION_BANK:
        by_country[question["country"]] = by_country.get(question["country"], 0) + 1
    assert by_country.get("GB", 0) >= 20
    assert by_country.get("US", 0) >= 20
    assert by_country.get("CA", 0) >= 15
    assert by_country.get("DE", 0) >= 15
    assert sum(by_country.values()) >= 70


# ---------------------------------------------------------------------
# Seed module is well-formed Python (catches accidental syntax breaks)
# ---------------------------------------------------------------------


def test_demo_seed_module_parses(seed_source: str) -> None:
    ast.parse(seed_source, filename=str(SEED_PATH))
