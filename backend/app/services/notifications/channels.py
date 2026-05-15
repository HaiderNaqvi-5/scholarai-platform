"""Notification channel stubs + plan-aware fan-out (PRD §0.6, Q1 retier).

Each ``send_*`` function is a log-only stub — no network I/O — so the priority
alert + deadline reminder Celery tasks stay deterministic in tests and CI.
``fan_out_for_plan`` encodes the Q1-retier channel matrix (WhatsApp-only
premium, SMS removed):

    free        -> email only
    pro         -> email only
    elite       -> email + WhatsApp
    institution -> email + WhatsApp
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.core.burn_cap import record_whatsapp
from app.models import User


logger = logging.getLogger(__name__)


PLAN_CHANNELS: dict[str, tuple[str, ...]] = {
    "free": ("email",),
    "pro": ("email",),
    "elite": ("email", "whatsapp"),
    "institution": ("email", "whatsapp"),
}


@dataclass
class NotificationResult:
    """Outcome of a fan-out — which channels fired, for assertions in tests."""

    channels: list[str] = field(default_factory=list)

    def add(self, channel: str) -> None:
        self.channels.append(channel)


async def send_email(user: User, message: str) -> bool:
    """Stub: log-only. Returns True so callers treat it as delivered."""
    logger.info("notify.email to=%s len=%d", getattr(user, "email", None), len(message or ""))
    return True


async def send_whatsapp(db, user: User, message: str) -> bool:
    """Stub: log-only WhatsApp send, also records a usage_ledger row.

    Q1 retier: every WhatsApp fan-out costs PKR_WHATSAPP_COST (see
    ``app.core.burn_cap.record_whatsapp``). Recording here keeps the burn-cap
    accounting honest no matter which task drives the send.
    """
    logger.info(
        "notify.whatsapp to=%s len=%d",
        getattr(user, "email", None),
        len(message or ""),
    )
    await record_whatsapp(db, user.id)
    return True


async def fan_out_for_plan(db, user: User, message: str) -> None:
    """Dispatch a message across the channels the user's plan unlocks."""
    for ch in PLAN_CHANNELS.get((user.plan or "free").lower(), ("email",)):
        if ch == "email":
            await send_email(user, message)
        elif ch == "whatsapp":
            await send_whatsapp(db, user, message)
