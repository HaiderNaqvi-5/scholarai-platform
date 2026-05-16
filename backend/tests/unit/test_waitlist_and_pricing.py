"""Unit tests for waitlist + pricing (Feature 10)."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.v1.routes.waitlist import _PRICING_BY_CURRENCY, _build_tiers
from app.main import create_app
from app.schemas.waitlist import WaitlistJoinRequest


def test_pricing_covers_all_required_currencies():
    assert set(_PRICING_BY_CURRENCY) == {"PKR", "GBP", "EUR", "AED", "USD"}


def test_pricing_pro_pkr_matches_prd_anchor():
    assert _PRICING_BY_CURRENCY["PKR"]["pro"] == "PKR 2,999/month"
    assert _PRICING_BY_CURRENCY["PKR"]["elite"] == "PKR 6,000/month"


def test_pricing_all_currencies_match_q1_retier():
    assert _PRICING_BY_CURRENCY["USD"]["pro"] == "$9.99/month"
    assert _PRICING_BY_CURRENCY["USD"]["elite"] == "$19.99/month"
    assert _PRICING_BY_CURRENCY["GBP"]["pro"] == "£8.49/month"
    assert _PRICING_BY_CURRENCY["GBP"]["elite"] == "£16.99/month"
    assert _PRICING_BY_CURRENCY["EUR"]["pro"] == "€9.49/month"
    assert _PRICING_BY_CURRENCY["EUR"]["elite"] == "€18.99/month"
    assert _PRICING_BY_CURRENCY["AED"]["pro"] == "AED 39/month"
    assert _PRICING_BY_CURRENCY["AED"]["elite"] == "AED 79/month"


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


def test_pricing_route_hides_institution_from_students():
    """PRD §0.6 trust boundary: the student-facing /upgrade page must not show
    the Institution tier. The default audience is student → 3 tiers."""
    client = TestClient(create_app())
    res = client.get("/api/v1/upgrade/pricing?currency=PKR")
    assert res.status_code == 200
    keys = [t["key"] for t in res.json()["tiers"]]
    assert keys == ["explorer", "pro", "elite"]
    assert "institution" not in keys


def test_pricing_route_exposes_institution_for_partners_audience():
    client = TestClient(create_app())
    res = client.get("/api/v1/upgrade/pricing?currency=PKR&audience=institution")
    assert res.status_code == 200
    keys = [t["key"] for t in res.json()["tiers"]]
    assert "institution" in keys
    assert len(keys) == 4


def test_pricing_route_rejects_unknown_audience():
    client = TestClient(create_app())
    res = client.get("/api/v1/upgrade/pricing?audience=bogus")
    assert res.status_code in (400, 422)


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
