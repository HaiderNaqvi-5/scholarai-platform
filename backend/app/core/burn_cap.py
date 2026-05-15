"""60% per-tier burn-cap accounting + LLM cost helpers.

Reads from / writes to `usage_ledger`. Wraps Anthropic LLM calls and WhatsApp
fan-out. Pre-flight `assert_within_burn_cap` raises HTTP 429 when the
month-to-date PKR spend plus the projected cost would exceed the tier budget
(60% of the user's subscription price). PKR_PER_USD is a coarse constant; tune
nightly if FX drift becomes material.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Final

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UsageLedger, User

PKR_PER_USD: Final[Decimal] = Decimal("280")

# (input_per_million_usd, output_per_million_usd)
PRICING_USD_PER_MTOK: Final[dict[str, tuple[Decimal, Decimal]]] = {
    "llm_haiku": (Decimal("1"), Decimal("5")),
    "llm_sonnet": (Decimal("3"), Decimal("15")),
}

WHATSAPP_COST_PKR: Final[Decimal] = Decimal("3")

# 60% of the monthly subscription price.
TIER_BUDGET_PKR: Final[dict[str, Decimal]] = {
    "free": Decimal("50"),
    "pro": Decimal("1799"),    # 2999 * 0.6
    "elite": Decimal("3600"),  # 6000 * 0.6
}

_INSTITUTION_BUDGET: Final[Decimal] = Decimal("999999")
_MICRO: Final[Decimal] = Decimal("1000000")


def _period() -> str:
    """Current UTC period stamp `YYYYMM` for ledger partitioning."""
    now = datetime.now(timezone.utc)
    return f"{now.year:04d}{now.month:02d}"


def llm_cost_pkr(kind: str, input_tokens: int, output_tokens: int) -> Decimal:
    """PKR cost of one Anthropic call, exact via Decimal."""
    in_price, out_price = PRICING_USD_PER_MTOK[kind]
    usd = (Decimal(input_tokens) * in_price + Decimal(output_tokens) * out_price) / Decimal(
        1_000_000
    )
    return usd * PKR_PER_USD


def tier_budget(user: User) -> Decimal:
    """Monthly burn budget in PKR for the user's plan (60% of subscription)."""
    plan = (user.plan or "free").lower()
    if plan == "institution":
        return _INSTITUTION_BUDGET
    return TIER_BUDGET_PKR.get(plan, Decimal("50"))


async def month_to_date_pkr(db: AsyncSession, user_id) -> Decimal:
    """Sum of ledger cost in PKR for `user_id` in the current period."""
    q = select(func.coalesce(func.sum(UsageLedger.cost_pkr_micro), 0)).where(
        UsageLedger.user_id == user_id,
        UsageLedger.period_yyyymm == _period(),
    )
    micro = (await db.execute(q)).scalar_one()
    return Decimal(int(micro)) / _MICRO


async def assert_within_burn_cap(
    db: AsyncSession, user: User, projected_pkr: Decimal
) -> None:
    """Raise 429 if the projected call would exceed the user's monthly budget."""
    spent = await month_to_date_pkr(db, user.id)
    budget = tier_budget(user)
    if spent + projected_pkr > budget:
        plan = (user.plan or "free").lower()
        raise HTTPException(
            status_code=429,
            detail={
                "error": "burn_cap_reached",
                "spent_pkr": str(spent.quantize(Decimal("0.01"))),
                "budget_pkr": str(budget),
                "upgrade_url": "/upgrade" if plan != "elite" else None,
                "message": (
                    "Monthly AI budget reached. Resets next month, or upgrade tier."
                ),
            },
        )


async def record_llm(
    db: AsyncSession,
    user_id,
    kind: str,
    input_tokens: int,
    output_tokens: int,
    endpoint: str,
) -> None:
    """Append a LLM call cost row to `usage_ledger`."""
    cost = llm_cost_pkr(kind, input_tokens, output_tokens)
    db.add(
        UsageLedger(
            user_id=user_id,
            period_yyyymm=_period(),
            kind=kind,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_pkr_micro=int(cost * _MICRO),
            endpoint=endpoint,
        )
    )
    await db.flush()


async def record_whatsapp(db: AsyncSession, user_id) -> None:
    """Append a WhatsApp send cost row to `usage_ledger`."""
    db.add(
        UsageLedger(
            user_id=user_id,
            period_yyyymm=_period(),
            kind="whatsapp",
            cost_pkr_micro=int(WHATSAPP_COST_PKR * _MICRO),
            endpoint="notifications.whatsapp",
        )
    )
    await db.flush()
