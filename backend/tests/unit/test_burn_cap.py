"""Unit tests for burn-cap accounting helpers (math only — no DB I/O)."""
from __future__ import annotations

import re
from decimal import Decimal

import pytest

from app.core.burn_cap import (
    PKR_PER_USD,
    TIER_BUDGET_PKR,
    WHATSAPP_COST_PKR,
    _period,
    llm_cost_pkr,
    tier_budget,
)


class _U:
    def __init__(self, plan: str | None) -> None:
        self.plan = plan
        self.id = "fake-uuid"


def test_haiku_cost_small_call() -> None:
    # 1000 input + 500 output tokens of Haiku 4.5
    # USD = (1000 * 1 + 500 * 5) / 1e6 = 0.0035
    # PKR = 0.0035 * 280 = 0.98 PKR
    c = llm_cost_pkr("llm_haiku", 1000, 500)
    assert Decimal("0.95") < c < Decimal("1.05")


def test_sonnet_cost_typical_sop() -> None:
    # 5000 input + 1800 output tokens of Sonnet 4.6
    # USD = (5000 * 3 + 1800 * 15) / 1e6 = 0.042
    # PKR = 0.042 * 280 = 11.76
    c = llm_cost_pkr("llm_sonnet", 5000, 1800)
    assert Decimal("11") < c < Decimal("13")


def test_unknown_kind_raises() -> None:
    with pytest.raises(KeyError):
        llm_cost_pkr("llm_phantom", 100, 100)


@pytest.mark.parametrize(
    "plan,expected",
    [
        ("free", Decimal("50")),
        ("pro", Decimal("1799")),
        ("elite", Decimal("3600")),
        (None, Decimal("50")),
        ("FREE", Decimal("50")),
    ],
)
def test_tier_budget(plan, expected) -> None:
    assert tier_budget(_U(plan)) == expected


def test_institution_budget_is_high() -> None:
    assert tier_budget(_U("institution")) >= Decimal("999999")


def test_whatsapp_cost_is_three_pkr() -> None:
    assert WHATSAPP_COST_PKR == Decimal("3")


def test_pkr_per_usd_constant() -> None:
    assert PKR_PER_USD == Decimal("280")


def test_period_is_yyyymm_string() -> None:
    p = _period()
    assert isinstance(p, str)
    assert re.fullmatch(r"\d{6}", p) is not None


def test_pro_budget_is_60_percent_of_2999() -> None:
    assert TIER_BUDGET_PKR["pro"] == Decimal("1799")


def test_elite_budget_is_60_percent_of_6000() -> None:
    assert TIER_BUDGET_PKR["elite"] == Decimal("3600")
