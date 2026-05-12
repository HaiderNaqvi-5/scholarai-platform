import pytest
from fastapi import HTTPException

from app.core.plan_guard import (
    PLAN_RANK,
    PRICE_BY_CURRENCY,
    assert_plan_or_raise,
    get_price_for_currency,
    has_plan_at_least,
)


class _FakeUser:
    def __init__(self, plan: str = "free", plan_currency: str = "PKR") -> None:
        self.plan = plan
        self.plan_currency = plan_currency


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
