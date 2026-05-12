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
    "PKR": "PKR 2,499/month",
    "GBP": "£6.99/month",
    "EUR": "€7.99/month",
    "AED": "AED 29/month",
    "USD": "$8.99/month",
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
