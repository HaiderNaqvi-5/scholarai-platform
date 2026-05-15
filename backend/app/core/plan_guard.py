"""Plan gating for the freemium model.

Build during Feature 1 so adding Stripe post-FYP is a one-sprint integration.
No payment flow lives here — only the gate + the upgrade-prompt payload.
"""

from __future__ import annotations

from functools import wraps
from typing import Callable, Iterable

from fastapi import Depends, HTTPException, Request

from app.core.dependencies import get_current_user
from app.models import User


PLAN_RANK: dict[str, int] = {
    "free": 0,
    "pro": 1,
    "elite": 2,
    "institution": 3,
}


PRICE_BY_CURRENCY: dict[str, str] = {
    "PKR": "PKR 2,999/month",
    "GBP": "£8.49/month",
    "EUR": "€9.49/month",
    "AED": "AED 39/month",
    "USD": "$9.99/month",
}


def get_price_for_currency(currency: str | None) -> str:
    return PRICE_BY_CURRENCY.get((currency or "PKR").upper(), PRICE_BY_CURRENCY["PKR"])


def user_plan_rank(user: User) -> int:
    return PLAN_RANK.get((user.plan or "free").lower(), 0)


def has_plan_at_least(user: User, *allowed_plans: str) -> bool:
    min_rank = min(PLAN_RANK[p] for p in allowed_plans)
    return user_plan_rank(user) >= min_rank


def raise_plan_required(
    user: User,
    allowed_plans: Iterable[str],
    *,
    message: str | None = None,
    extra: dict | None = None,
) -> None:
    """Raise HTTP 402 with currency-correct upgrade payload."""
    price = get_price_for_currency(user.plan_currency)
    allowed_list = list(allowed_plans)
    detail: dict = {
        "error": "plan_required",
        "required_plan": allowed_list,
        "current_plan": user.plan,
        "upgrade_url": "/upgrade",
        "price": price,
        "message": message
        or f"Upgrade to ScholarAI Pro — {price}. Less than one consultant meeting.",
    }
    if extra:
        detail.update(extra)
    raise HTTPException(status_code=402, detail=detail)


def require_plan(*allowed_plans: str) -> Callable:
    """FastAPI route decorator. Usage: ``@require_plan("pro", "elite", "institution")``.

    Returns HTTP 402 with currency-correct upgrade prompt when the caller is below
    the minimum rank in ``allowed_plans``.
    """
    if not allowed_plans:
        raise ValueError("require_plan() needs at least one plan tier")
    for plan in allowed_plans:
        if plan not in PLAN_RANK:
            raise ValueError(f"unknown plan tier: {plan!r}")

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            **kwargs,
        ):
            if not has_plan_at_least(current_user, *allowed_plans):
                raise_plan_required(current_user, allowed_plans)
            kwargs["current_user"] = current_user
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def assert_plan_or_raise(
    user: User,
    *allowed_plans: str,
    message: str | None = None,
    extra: dict | None = None,
) -> None:
    """Imperative version of require_plan — call inside a service when the gate
    depends on per-row state (e.g. user already has 1 free SOP)."""
    if not has_plan_at_least(user, *allowed_plans):
        raise_plan_required(user, allowed_plans, message=message, extra=extra)


# Q1 retier caps -----------------------------------------------------------
MATCH_CAP: dict[str, int] = {"free": 3, "pro": 6, "elite": 12, "institution": 12}
TRACKER_CAP: dict[str, int] = {"free": 3, "pro": 6, "elite": 12, "institution": 50}
MONTHLY_SOP_CAP: dict[str, int] = {"free": 0, "pro": 5, "elite": 10, "institution": 50}
LIFETIME_FREE_SOP: int = 1
PRO_BLURRED_BEST_FIT_COUNT: int = 3

BEST_FIT_REVEAL_PLANS: frozenset[str] = frozenset({"elite", "institution"})
PREMIUM_VISIBLE_PLANS: frozenset[str] = frozenset({"pro", "elite", "institution"})


def can_reveal_best_fit(user: User) -> bool:
    """True when the user's plan exposes the eligible (best-fit) match bucket."""
    return (user.plan or "free").lower() in BEST_FIT_REVEAL_PLANS


def can_see_premium(user: User) -> bool:
    """True when the user's plan can view premium-tier scholarships."""
    return (user.plan or "free").lower() in PREMIUM_VISIBLE_PLANS
