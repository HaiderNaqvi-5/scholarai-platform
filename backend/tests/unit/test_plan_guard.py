import pytest
from fastapi import HTTPException

from app.core.plan_guard import (
    PLAN_RANK,
    PRICE_BY_CURRENCY,
    assert_plan_or_raise,
    get_price_for_currency,
    has_plan_at_least,
)

from datetime import datetime, timedelta, timezone

from app.core.plan_guard import (
    can_reveal_best_fit,
    can_see_premium,
    user_plan_rank,
)


class _FakeUser:
    def __init__(
        self,
        plan: str = "free",
        plan_currency: str = "PKR",
        plan_expires_at: "datetime | None" = None,
    ) -> None:
        self.plan = plan
        self.plan_currency = plan_currency
        self.plan_expires_at = plan_expires_at


def test_plan_rank_order() -> None:
    assert PLAN_RANK["free"] < PLAN_RANK["pro"] < PLAN_RANK["elite"] < PLAN_RANK["institution"]


def test_price_by_currency_covers_five_currencies() -> None:
    assert set(PRICE_BY_CURRENCY) == {"PKR", "GBP", "EUR", "AED", "USD"}


def test_get_price_defaults_to_pkr_on_unknown_or_missing() -> None:
    assert get_price_for_currency(None).startswith("PKR")
    assert get_price_for_currency("xyz").startswith("PKR")
    assert get_price_for_currency("gbp") == PRICE_BY_CURRENCY["GBP"]


def test_has_plan_at_least() -> None:
    free = _FakeUser("free")
    pro = _FakeUser("pro")
    elite = _FakeUser("elite")
    assert not has_plan_at_least(free, "pro", "elite", "institution")
    assert has_plan_at_least(pro, "pro", "elite", "institution")
    assert has_plan_at_least(elite, "pro", "elite", "institution")


def test_assert_plan_raises_402_with_currency_aware_price() -> None:
    user = _FakeUser("free", plan_currency="GBP")
    with pytest.raises(HTTPException) as excinfo:
        assert_plan_or_raise(user, "pro")
    err = excinfo.value
    assert err.status_code == 402
    assert err.detail["price"] == PRICE_BY_CURRENCY["GBP"]
    assert err.detail["required_plan"] == ["pro"]
    assert err.detail["current_plan"] == "free"


def test_assert_plan_passes_for_sufficient_plan() -> None:
    user = _FakeUser("elite")
    assert_plan_or_raise(user, "pro", "elite", "institution")  # no raise


# R4-PLAN-EXPIRY: an expired paid plan must drop to free rank in real time.
def test_user_plan_rank_downgrades_expired_plan_to_free() -> None:
    past = datetime.now(timezone.utc) - timedelta(days=1)
    assert user_plan_rank(_FakeUser("elite", plan_expires_at=past)) == PLAN_RANK["free"]


def test_user_plan_rank_honors_future_expiry() -> None:
    future = datetime.now(timezone.utc) + timedelta(days=30)
    assert user_plan_rank(_FakeUser("elite", plan_expires_at=future)) == PLAN_RANK["elite"]


def test_user_plan_rank_unchanged_when_no_expiry() -> None:
    assert user_plan_rank(_FakeUser("elite")) == PLAN_RANK["elite"]


def test_user_plan_rank_treats_naive_expiry_as_utc() -> None:
    naive_past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
    assert user_plan_rank(_FakeUser("pro", plan_expires_at=naive_past)) == PLAN_RANK["free"]


def test_assert_plan_raises_for_expired_paid_plan() -> None:
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    with pytest.raises(HTTPException) as excinfo:
        assert_plan_or_raise(_FakeUser("elite", plan_expires_at=past), "pro", "elite", "institution")
    assert excinfo.value.status_code == 402


def test_premium_visibility_revoked_when_expired() -> None:
    past = datetime.now(timezone.utc) - timedelta(days=2)
    expired = _FakeUser("elite", plan_expires_at=past)
    assert can_see_premium(expired) is False
    assert can_reveal_best_fit(expired) is False
