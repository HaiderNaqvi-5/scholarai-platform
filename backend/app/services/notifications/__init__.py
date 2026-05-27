"""Notification channel stubs (PRD §0.6).

FYP-scoped: no real Twilio / WhatsApp Business / SMTP integration. Channels
log-only so Celery tasks, tests, and CI run offline. Post-FYP, swap the stub
bodies for real providers without changing call sites.
"""

from app.services.notifications.channels import (
    PLAN_CHANNELS,
    NotificationResult,
    fan_out_for_plan,
    send_email,
    send_email_notification,
    send_templated_email_best_effort,
    send_whatsapp,
)

__all__ = [
    "PLAN_CHANNELS",
    "NotificationResult",
    "fan_out_for_plan",
    "send_email",
    "send_email_notification",
    "send_templated_email_best_effort",
    "send_whatsapp",
]
