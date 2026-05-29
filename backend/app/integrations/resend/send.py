from __future__ import annotations

import os
import re
from typing import Literal

import resend
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.config import settings
from app.integrations.resend.client import configure
from app.integrations.resend.templates import (
    welcome,
    data_export_ready,
    account_deletion_scheduled,
    account_deletion_cancelled,
    waitlist_confirmation,
    deadline_reminder,
    priority_alert,
)

_TEMPLATES = {
    "welcome": welcome.render,
    "data_export_ready": data_export_ready.render,
    "account_deletion_scheduled": account_deletion_scheduled.render,
    "account_deletion_cancelled": account_deletion_cancelled.render,
    "waitlist_confirmation": waitlist_confirmation.render,
    "deadline_reminder": deadline_reminder.render,
    "priority_alert": priority_alert.render,
}

_CRLF = re.compile(r"[\r\n\x00]")


class TransactionalRequest(BaseModel):
    to: EmailStr
    template: Literal[
        "welcome",
        "data_export_ready",
        "account_deletion_scheduled",
        "account_deletion_cancelled",
        "waitlist_confirmation",
        "deadline_reminder",
        "priority_alert",
    ]
    context: dict = Field(default_factory=dict)

    @field_validator("to", mode="before")
    @classmethod
    def reject_crlf(cls, v: str) -> str:
        if isinstance(v, str) and _CRLF.search(v):
            raise ValueError("CRLF / null in email address")
        return v


def send_transactional(*, to: str, template: str, context: dict) -> str:
    req = TransactionalRequest(to=to, template=template, context=context)
    configure()
    subject, html, text = _TEMPLATES[req.template](req.context)
    from_address = os.environ.get("RESEND_FROM_ADDRESS") or settings.RESEND_FROM_ADDRESS
    response = resend.Emails.send({
        "from": from_address,
        "to": [req.to],
        "subject": subject,
        "html": html,
        "text": text,
    })
    # resend SDK 2.5.1 returns a dict ({"id": ...}); older/mocked shapes may
    # expose `.id` as an attribute. Handle both so a real send does not raise.
    if isinstance(response, dict):
        return response["id"]
    return response.id
