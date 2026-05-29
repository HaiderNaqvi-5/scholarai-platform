"""Verify account-deletion endpoints dispatch transactional emails."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.api.v1.routes import privacy as privacy_route
from app.schemas.privacy import DataDeletionCreateRequest


def _user():
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="delete-me@example.com",
        full_name="Deleter Person",
    )


@pytest.mark.asyncio
async def test_schedule_deletion_sends_email(monkeypatch):
    sent: list[dict] = []

    def fake_send(*, to, template, context, source):
        sent.append({"to": to, "template": template, "context": context, "source": source})
        return "msg_sched"

    monkeypatch.setattr(privacy_route, "send_templated_email_best_effort", fake_send)
    monkeypatch.setattr(privacy_route.settings, "FRONTEND_BASE_URL", "https://aidwiseai.com")

    scheduled_for_dt = datetime(2026, 6, 26, tzinfo=timezone.utc)
    record = SimpleNamespace(
        id=uuid.uuid4(),
        status="pending",
        requested_at=datetime.now(timezone.utc),
        scheduled_for=scheduled_for_dt,
        cancelled_at=None,
        executed_at=None,
    )

    class FakeDeletionService:
        def __init__(self, db): ...
        async def schedule(self, user, *, reason): return record

    monkeypatch.setattr(privacy_route, "DeletionService", FakeDeletionService)

    user = _user()
    response = await privacy_route.schedule_account_deletion(
        payload=DataDeletionCreateRequest(reason="test"),
        current_user=user,
        db=SimpleNamespace(),
    )

    assert response.status == "pending"
    assert len(sent) == 1
    assert sent[0]["template"] == "account_deletion_scheduled"
    assert sent[0]["to"] == "delete-me@example.com"
    assert sent[0]["context"]["name"] == "Deleter Person"
    assert sent[0]["context"]["scheduled_deletion_at"] == "2026-06-26"
    assert sent[0]["context"]["cancel_url"] == "https://aidwiseai.com/settings/privacy"


@pytest.mark.asyncio
async def test_cancel_deletion_sends_email(monkeypatch):
    sent: list[dict] = []

    def fake_send(*, to, template, context, source):
        sent.append({"to": to, "template": template, "source": source})
        return "msg_cancel"

    monkeypatch.setattr(privacy_route, "send_templated_email_best_effort", fake_send)

    class FakeDeletionService:
        def __init__(self, db): ...
        async def cancel(self, user_id): return True

    monkeypatch.setattr(privacy_route, "DeletionService", FakeDeletionService)

    user = _user()
    result = await privacy_route.cancel_account_deletion(
        current_user=user,
        db=SimpleNamespace(),
    )

    assert result is None  # 204
    assert len(sent) == 1
    assert sent[0]["template"] == "account_deletion_cancelled"
    assert sent[0]["to"] == "delete-me@example.com"
    assert sent[0]["source"] == "account_deletion_cancelled"


@pytest.mark.asyncio
async def test_cancel_deletion_no_pending_no_email(monkeypatch):
    """Cancel must NOT send email when no pending deletion exists (404 path)."""
    from fastapi import HTTPException

    sent: list = []
    monkeypatch.setattr(
        privacy_route, "send_templated_email_best_effort",
        lambda **kw: sent.append(kw),
    )

    class FakeDeletionService:
        def __init__(self, db): ...
        async def cancel(self, user_id): return False

    monkeypatch.setattr(privacy_route, "DeletionService", FakeDeletionService)

    with pytest.raises(HTTPException) as exc:
        await privacy_route.cancel_account_deletion(
            current_user=_user(),
            db=SimpleNamespace(),
        )
    assert exc.value.status_code == 404
    assert sent == []
