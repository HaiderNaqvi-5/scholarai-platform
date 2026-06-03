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


from app.services.llm.anthropic_client import (
    _CACHED_SYSTEM_DISCOUNT,
    _estimate_input_tokens,
)


def _full_price_tokens(system_prompt: str, user_prompt: str) -> int:
    """Pre-fix behaviour: whole blob at 4 chars/token (no cache discount)."""
    import json as _json

    blob = _json.dumps(
        {"system": system_prompt or "", "user": user_prompt or ""},
        default=str,
    )
    return max(1, len(blob) // 4)


def test_estimate_discounts_cached_system_prompt() -> None:
    # A large static system prefix (the cached ephemeral block) plus a small
    # user prompt. The cached prefix must be discounted, so the estimate is
    # strictly lower than charging the whole blob at full price.
    system_prompt = "S" * 4000  # ~1000 tokens of static cached prefix
    user_prompt = "U" * 400  # ~100 tokens of per-call user content
    estimate = _estimate_input_tokens(system_prompt, user_prompt)
    assert estimate < _full_price_tokens(system_prompt, user_prompt)


def test_estimate_counts_user_prompt_at_full_price() -> None:
    # With an empty system prompt, the discount has nothing to bite on, so the
    # estimate must equal the old full-price behaviour for the user prompt.
    user_prompt = "U" * 4000
    assert _estimate_input_tokens("", user_prompt) == _full_price_tokens(
        "", user_prompt
    )


def test_estimate_uses_cache_read_discount_fraction() -> None:
    # The system contribution should be the system token count scaled by the
    # cache-read discount (Anthropic bills cached reads at ~0.1x base input).
    # Verify the discount constant is the published cache-read fraction and
    # that the estimate moves with it.
    assert _CACHED_SYSTEM_DISCOUNT == 0.1
    system_prompt = "S" * 8000  # ~2000 system tokens
    no_user = _estimate_input_tokens(system_prompt, "")
    # ~2000 system tokens * 0.1 == ~200; allow slack for json framing / floor.
    assert 150 <= no_user <= 300


def test_estimate_floor_is_one() -> None:
    # Degenerate empty inputs still return at least 1 token (burn-cap math
    # must never see 0 and treat a real call as free).
    assert _estimate_input_tokens("", "") >= 1
