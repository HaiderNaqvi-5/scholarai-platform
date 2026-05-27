from __future__ import annotations

import os
import re
from typing import Literal

import resend
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.config import settings
from app.integrations.resend.client import configure
from app.integrations.resend.templates import welcome, data_export_ready

_TEMPLATES = {
    "welcome": welcome.render,
    "data_export_ready": data_export_ready.render,
}

_CRLF = re.compile(r"[\r\n\x00]")


class TransactionalRequest(BaseModel):
    to: EmailStr
    template: Literal["welcome", "data_export_ready"]
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
    # Prefer live env var so monkeypatch.setenv works in tests without
    # re-instantiating the Settings singleton.
    from_address = os.environ.get("RESEND_FROM_ADDRESS") or settings.RESEND_FROM_ADDRESS
    response = resend.Emails.send({
        "from": from_address,
        "to": [req.to],
        "subject": subject,
        "html": html,
        "text": text,
    })
    return response.id
