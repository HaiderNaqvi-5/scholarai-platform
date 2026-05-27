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
from app.integrations.resend.send import send_transactional
from app.models import User


logger = logging.getLogger(__name__)


_DEFAULT_EMAIL_SUBJECT = "AidwiseAI notification"
_RESEND_ENDPOINT = "https://api.resend.com/emails"


def _sanitize_header(value: str) -> str:
    """Strip CR/LF + NUL to prevent header injection (S13).

    Resend normalises subjects and recipient lists, but a `\\r\\n` in
    user-supplied input could still smuggle headers in some edge cases.
    Defence-in-depth even though the provider catches most.
    """
    if not value:
        return ""
    cleaned = (
        value.replace("\r", " ").replace("\n", " ").replace("\x00", "").strip()
    )
    return cleaned[:998]  # RFC 5322 max line length


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
    """Send a transactional email via Resend when configured.

    Falls back to log-only behaviour when ``RESEND_API_KEY`` or
    ``RESEND_FROM_ADDRESS`` are absent — this keeps CI + offline dev
    deterministic and means a Resend outage degrades to "alerts logged but
    not sent" rather than 5xx-ing the calling task. Returns True iff Resend
    accepted the request (or we successfully logged the stub message).
    """

    recipient = getattr(user, "email", None)
    if not recipient:
        logger.warning("notify.email skipped: user has no email")
        return False

    if not settings.RESEND_API_KEY or not settings.RESEND_FROM_ADDRESS:
        logger.info(
            "notify.email (log-only, resend unconfigured) to=%s len=%d",
            recipient,
            len(message or ""),
        )
        return True

    effective_subject = _sanitize_header(subject or _DEFAULT_EMAIL_SUBJECT)
    safe_recipient = _sanitize_header(recipient)
    sender = (
        f"{_sanitize_header(settings.BRAND_DISPLAY_NAME)} "
        f"<{settings.RESEND_FROM_ADDRESS}>"
    )
    payload: dict[str, object] = {
        "from": sender,
        "to": [safe_recipient],
        "subject": effective_subject,
        "text": message,
    }
    if html:
        payload["html"] = html

    try:
        async with httpx.AsyncClient(timeout=settings.RESEND_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                _RESEND_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except httpx.HTTPError as exc:
        logger.warning("notify.email resend transport error to=%s err=%r", recipient, exc)
        return False

    if resp.status_code >= 400:
        logger.warning(
            "notify.email resend rejected to=%s status=%d body=%s",
            recipient,
            resp.status_code,
            resp.text[:200],
        )
        return False

    logger.info("notify.email resend accepted to=%s subject=%r", recipient, effective_subject)
    return True


def send_email_notification(*, to: str, template: str, context: dict) -> str:
    """Send a templated transactional email via Resend.

    Thin wrapper that surfaces the schema-validated send path
    (``send_transactional``) at the notifications layer. New callers should
    prefer this over the free-text ``send_email`` so all outbound mail flows
    through a registered template with CRLF rejection.
    """
    return send_transactional(to=to, template=template, context=context)


def send_templated_email_best_effort(
    *, to: str, template: str, context: dict, source: str
) -> str | None:
    """Wrap send_email_notification with try/except so callers never raise.

    Every transactional touchpoint (welcome, data-export, deletion, waitlist)
    treats email delivery as best-effort: the underlying state change has
    already committed, and a Resend outage must not propagate as a 5xx.

    ``source`` is a short tag for logs ("welcome", "data_export", etc.).
    Returns the Resend message id on success, or None on any failure.
    """
    try:
        return send_email_notification(to=to, template=template, context=context)
    except Exception as exc:  # noqa: BLE001 — best-effort channel
        logger.warning("notify.email %s failed to=%s err=%r", source, to, exc)
        return None


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


async def fan_out_for_plan(
    db,
    user: User,
    *,
    email_template: str,
    email_context: dict,
    whatsapp_message: str,
) -> None:
    """Dispatch a notification across the channels the user's plan unlocks.

    Email uses the schema-validated template registry via the best-effort
    wrapper (Resend outage never bubbles up). WhatsApp gets a short
    plaintext because WhatsApp Business doesn't render HTML and has a
    different brevity budget — the caller supplies both.
    """
    for ch in PLAN_CHANNELS.get((user.plan or "free").lower(), ("email",)):
        if ch == "email":
            send_templated_email_best_effort(
                to=user.email,
                template=email_template,
                context=email_context,
                source=email_template,
            )
        elif ch == "whatsapp":
            await send_whatsapp(db, user, whatsapp_message)
