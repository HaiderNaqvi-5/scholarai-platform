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

import httpx

from app.core.burn_cap import record_whatsapp
from app.core.config import settings
from app.models import User


logger = logging.getLogger(__name__)


_DEFAULT_EMAIL_SUBJECT = "AidwiseAI notification"


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


async def send_email(
    user: User,
    message: str,
    *,
    subject: str | None = None,
    html: str | None = None,
) -> bool:
    """Send a transactional email via Mailgun when configured.

    Falls back to log-only behaviour when ``MAILGUN_API_KEY`` or
    ``MAILGUN_DOMAIN`` are absent — this keeps CI + offline dev deterministic
    and means a Mailgun outage degrades to "alerts logged but not sent"
    rather than 5xx-ing the calling task. Returns True iff Mailgun accepted
    the request (or we successfully logged the stub message).

    The ``subject`` arg is optional so existing callers (``alert_tasks``,
    ``reminder_tasks``) that pass only ``(user, message)`` keep working;
    when absent we use a generic ``_DEFAULT_EMAIL_SUBJECT`` so the inbox
    never shows an empty subject line.
    """

    recipient = getattr(user, "email", None)
    if not recipient:
        logger.warning("notify.email skipped: user has no email")
        return False

    if not settings.MAILGUN_API_KEY or not settings.MAILGUN_DOMAIN:
        logger.info(
            "notify.email (log-only, mailgun unconfigured) to=%s len=%d",
            recipient,
            len(message or ""),
        )
        return True

    effective_subject = subject or _DEFAULT_EMAIL_SUBJECT
    sender = (
        f"{settings.BRAND_DISPLAY_NAME} "
        f"<{settings.EMAIL_FROM_LOCALPART}@{settings.MAILGUN_DOMAIN}>"
    )
    url = f"{settings.MAILGUN_BASE_URL.rstrip('/')}/{settings.MAILGUN_DOMAIN}/messages"
    data = {
        "from": sender,
        "to": [recipient],
        "subject": effective_subject,
        "text": message,
    }
    if html:
        data["html"] = html

    try:
        async with httpx.AsyncClient(timeout=settings.MAILGUN_TIMEOUT_SECONDS) as client:
            resp = await client.post(url, auth=("api", settings.MAILGUN_API_KEY), data=data)
    except httpx.HTTPError as exc:
        logger.warning("notify.email mailgun transport error to=%s err=%r", recipient, exc)
        return False

    if resp.status_code >= 400:
        logger.warning(
            "notify.email mailgun rejected to=%s status=%d body=%s",
            recipient,
            resp.status_code,
            resp.text[:200],
        )
        return False

    logger.info("notify.email mailgun accepted to=%s subject=%r", recipient, effective_subject)
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
