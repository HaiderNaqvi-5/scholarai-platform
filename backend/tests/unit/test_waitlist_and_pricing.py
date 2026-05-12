"""Unit tests for waitlist + pricing (Feature 10)."""

import pytest
from pydantic import ValidationError

from app.api.v1.routes.waitlist import _PRICING_BY_CURRENCY, _build_tiers
from app.schemas.waitlist import WaitlistJoinRequest


def test_pricing_covers_all_required_currencies():
    assert set(_PRICING_BY_CURRENCY) == {"PKR", "GBP", "EUR", "AED", "USD"}


def test_pricing_pro_pkr_matches_prd_anchor():
    assert _PRICING_BY_CURRENCY["PKR"]["pro"] == "PKR 2,499/month"
    assert _PRICING_BY_CURRENCY["PKR"]["elite"] == "PKR 7,999/month"


def test_pricing_tier_count_is_four():
    assert len(_build_tiers("PKR")) == 4


def test_pricing_recommended_tier_is_pro():
    tiers = _build_tiers("PKR")
    recommended = [t for t in tiers if t.is_recommended]
    assert len(recommended) == 1
    assert recommended[0].key == "pro"


def test_pricing_elite_lists_line_feedback_and_transcript():
    tiers = _build_tiers("PKR")
    elite = next(t for t in tiers if t.key == "elite")
    body = " ".join(elite.bullet_features).lower()
    assert "line-by-line" in body
    assert "transcript" in body


def test_waitlist_request_rejects_unknown_plan():
    with pytest.raises(ValidationError):
        WaitlistJoinRequest(email="x@y.com", plan="free")


def test_waitlist_request_rejects_unknown_currency():
    with pytest.raises(ValidationError):
        WaitlistJoinRequest(email="x@y.com", plan="pro", currency="INR")


def test_waitlist_request_normalises_email_and_country():
    req = WaitlistJoinRequest(
        email="  Foo@Example.COM ",
        plan="pro",
        currency="pkr",
        country="pk",
    )
    assert req.email == "foo@example.com"
    assert req.currency == "PKR"
    assert req.country == "PK"
