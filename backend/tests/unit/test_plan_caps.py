"""Per-plan caps + reveal gates for Q1 retier (Pro 2999 / Elite 6000)."""
from __future__ import annotations

import pytest

from app.core.plan_guard import (
    BEST_FIT_REVEAL_PLANS,
    LIFETIME_FREE_SOP,
    MATCH_CAP,
    MONTHLY_SOP_CAP,
    PREMIUM_VISIBLE_PLANS,
    PRICE_BY_CURRENCY,
    PRO_BLURRED_BEST_FIT_COUNT,
    TRACKER_CAP,
    can_reveal_best_fit,
    can_see_premium,
)


class _U:  # minimal stand-in for User in helper-level tests
    def __init__(self, plan: str | None) -> None:
        self.plan = plan


@pytest.mark.parametrize(
    "plan,matches,tracker,sop",
    [
        ("free", 3, 3, 0),
        ("pro", 6, 6, 5),
        ("elite", 12, 12, 10),
        ("institution", 12, 50, 50),
    ],
)
def test_caps_per_plan(plan: str, matches: int, tracker: int, sop: int) -> None:
    assert MATCH_CAP[plan] == matches
    assert TRACKER_CAP[plan] == tracker
    assert MONTHLY_SOP_CAP[plan] == sop


def test_lifetime_free_sop_is_one() -> None:
    assert LIFETIME_FREE_SOP == 1


def test_pro_blurred_count_is_three() -> None:
    assert PRO_BLURRED_BEST_FIT_COUNT == 3


def test_best_fit_reveal_plans() -> None:
    assert BEST_FIT_REVEAL_PLANS == frozenset({"elite", "institution"})


def test_premium_visible_plans() -> None:
    assert PREMIUM_VISIBLE_PLANS == frozenset({"pro", "elite", "institution"})


@pytest.mark.parametrize(
    "plan,can_best,can_prem",
    [
        ("free", False, False),
        ("pro", False, True),
        ("elite", True, True),
        ("institution", True, True),
        (None, False, False),
    ],
)
def test_reveal_gates(plan: str | None, can_best: bool, can_prem: bool) -> None:
    u = _U(plan)
    assert can_reveal_best_fit(u) is can_best
    assert can_see_premium(u) is can_prem


def test_pro_price_pkr_is_2999() -> None:
    assert PRICE_BY_CURRENCY["PKR"] == "PKR 2,999/month"
    assert PRICE_BY_CURRENCY["USD"] == "$9.99/month"
