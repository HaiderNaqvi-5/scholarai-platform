"""Verify waitlist join dispatches a waitlist_confirmation email."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.api.v1.routes import waitlist as waitlist_route
from app.schemas.waitlist import WaitlistJoinRequest


class _FakeResult:
    def __init__(self, row):
        self._row = row

    def scalar_one_or_none(self):
        return self._row


class _FakeDB:
    """Minimal async DB stub for the waitlist endpoint."""

    def __init__(self, prior_row=None):
        self._row = prior_row
        self._added = []

    async def execute(self, _stmt):
        return _FakeResult(self._row)

    def add(self, obj):
        self._added.append(obj)
        self._row = obj
        # Populate the autogen fields that flush would normally fill.
        obj.id = uuid.uuid4()
        obj.created_at = datetime.now(timezone.utc)

    async def flush(self):
        pass

    async def refresh(self, _obj):
        pass

    async def commit(self):
        pass


@pytest.mark.asyncio
async def test_join_waitlist_sends_email(monkeypatch):
    sent: list[dict] = []

    def fake_send(*, to, template, context, source):
        sent.append({"to": to, "template": template, "context": context, "source": source})
        return "msg_wl"

    monkeypatch.setattr(waitlist_route, "send_templated_email_best_effort", fake_send)

    payload = WaitlistJoinRequest(
        email="prospect@example.com", plan="elite", currency="GBP", country="GB",
    )
    db = _FakeDB(prior_row=None)
    response = await waitlist_route.join_waitlist(payload=payload, db=db)

    assert response.email == "prospect@example.com"
    assert response.plan == "elite"
    assert len(sent) == 1
    assert sent[0]["to"] == "prospect@example.com"
    assert sent[0]["template"] == "waitlist_confirmation"
    assert sent[0]["context"] == {"plan": "elite", "currency": "GBP"}
    assert sent[0]["source"] == "waitlist"


@pytest.mark.asyncio
async def test_join_waitlist_email_swallows_failure(monkeypatch, caplog):
    """If Resend errors, the endpoint still returns 201 (best-effort)."""

    def boom(**_):
        raise RuntimeError("resend down")

    # Patch the path the helper calls under the hood so the real best-effort
    # wrapper catches the error.
    monkeypatch.setattr(
        "app.services.notifications.channels.send_email_notification", boom,
    )

    payload = WaitlistJoinRequest(
        email="prospect2@example.com", plan="pro", currency="PKR",
    )
    db = _FakeDB(prior_row=None)

    with caplog.at_level("WARNING"):
        response = await waitlist_route.join_waitlist(payload=payload, db=db)

    assert response.email == "prospect2@example.com"
    assert "waitlist failed" in caplog.text
