"""
Task 6: Clerk webhook handler tests.

Test approach: TestClient + dependency_overrides[get_db] with a duck-typed
fake async session.  This matches the pattern used in test_public_scholarships.py
and avoids spinning up a real PostgreSQL / async SQLite engine.

The fake session stores User objects in an in-memory list, and the handler
interacts with it via the same async execute / commit interface.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from math import floor
import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_db


# ─── Fake async session ───────────────────────────────────────────────────────

class _FakeResult:
    def __init__(self, row):
        self._row = row

    def scalar_one_or_none(self):
        return self._row


class _FakeAsyncSession:
    """Duck-typed async session that stores User rows in memory."""

    def __init__(self):
        self._store: list = []
        self.committed = False

    def add(self, obj):
        self._store.append(obj)

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        pass  # no-op; row was already in memory

    async def execute(self, stmt):
        # Extract WHERE clause value by compiling with literal binds.
        try:
            rendered = str(
                stmt.compile(compile_kwargs={"literal_binds": True})
            ).lower()
        except Exception:
            rendered = str(stmt).lower()

        # Match by clerk_user_id OR email — _user_exists queries both.
        for obj in self._store:
            cuid = (obj.clerk_user_id or "").lower()
            if cuid and cuid in rendered:
                return _FakeResult(obj)
            email = (obj.email or "").lower()
            if email and email in rendered:
                return _FakeResult(obj)
        return _FakeResult(None)

    def get_store(self):
        return self._store


# ─── Svix signing helper ──────────────────────────────────────────────────────

def _sign_payload(secret: str, payload: dict) -> tuple[str, str, str]:
    """Return (svix-id, svix-timestamp, svix-signature) headers."""
    from svix.webhooks import Webhook

    msg_id = f"msg_{uuid.uuid4().hex}"
    now = datetime.now(timezone.utc)
    timestamp_str = str(floor(now.timestamp()))
    body_str = json.dumps(payload)

    wh = Webhook(secret)
    # sign() takes a datetime object; returns "v1,<base64>"
    sig = wh.sign(msg_id=msg_id, timestamp=now, data=body_str)
    return msg_id, timestamp_str, sig


# ─── Tests ────────────────────────────────────────────────────────────────────

TEST_SECRET = "whsec_" + "A" * 32  # valid whsec_ prefix + 32 chars


@pytest.fixture
def webhook_app(monkeypatch):
    """App fixture with CLERK_WEBHOOK_SECRET configured."""
    monkeypatch.setattr(settings, "CLERK_WEBHOOK_SECRET", TEST_SECRET)
    from app.main import create_app
    app = create_app()
    return app


@pytest.fixture
def webhook_client(webhook_app):
    return TestClient(webhook_app)


def test_webhook_rejects_bad_signature(webhook_app, webhook_client):
    """Garbage svix headers should yield 401."""
    async def override_db():
        yield _FakeAsyncSession()

    webhook_app.dependency_overrides[get_db] = override_db

    payload = json.dumps({"type": "user.created", "data": {"id": "user_bad"}})
    response = webhook_client.post(
        "/api/v1/webhooks/clerk",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "svix-id": "msg_bad",
            "svix-timestamp": "1234567890",
            "svix-signature": "v1,invalidsignature",
        },
    )
    webhook_app.dependency_overrides.clear()

    assert response.status_code == 401


def test_user_created_event_creates_local_user(webhook_app, webhook_client, monkeypatch):
    """A signed user.created event should create a new User row."""
    import app.api.v1.routes.clerk_webhook as clerk_webhook_route

    fake_session = _FakeAsyncSession()

    async def override_db():
        yield fake_session

    # Patch the name in the route module's namespace (where it was imported).
    async def fake_ensure(clerk_user_id, *, session, clerk_api=None):
        from app.models.models import User
        u = User(
            email="created@example.com",
            password_hash="clerk:placeholder",
            clerk_user_id=clerk_user_id,
            full_name="Created User",
        )
        session.add(u)
        await session.commit()
        return u

    monkeypatch.setattr(clerk_webhook_route, "ensure_local_user_async", fake_ensure)
    webhook_app.dependency_overrides[get_db] = override_db

    payload_dict = {
        "type": "user.created",
        "data": {
            "id": "user_created_001",
            "email_addresses": [{"id": "e1", "email_address": "created@example.com"}],
            "primary_email_address_id": "e1",
            "first_name": "Created",
            "last_name": "User",
        },
    }
    msg_id, ts, sig = _sign_payload(TEST_SECRET, payload_dict)
    body_str = json.dumps(payload_dict)

    response = webhook_client.post(
        "/api/v1/webhooks/clerk",
        content=body_str,
        headers={
            "Content-Type": "application/json",
            "svix-id": msg_id,
            "svix-timestamp": ts,
            "svix-signature": sig,
        },
    )
    webhook_app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    assert response.json() == {"status": "ok"}

    store = fake_session.get_store()
    assert len(store) == 1
    assert store[0].clerk_user_id == "user_created_001"
    assert store[0].email == "created@example.com"


def test_user_deleted_event_soft_deletes(webhook_app, webhook_client, monkeypatch):
    """A signed user.deleted event should set is_active=False on the user."""
    from app.models.models import User

    # Pre-seed a user in the fake session.
    fake_session = _FakeAsyncSession()
    existing_user = User(
        email="delete@example.com",
        password_hash="hash",
        clerk_user_id="user_existing_for_deletion",
        full_name="To Delete",
    )
    existing_user.is_active = True
    fake_session._store.append(existing_user)

    async def override_db():
        yield fake_session

    webhook_app.dependency_overrides[get_db] = override_db

    payload_dict = {
        "type": "user.deleted",
        "data": {"id": "user_existing_for_deletion"},
    }
    msg_id, ts, sig = _sign_payload(TEST_SECRET, payload_dict)
    body_str = json.dumps(payload_dict)

    response = webhook_client.post(
        "/api/v1/webhooks/clerk",
        content=body_str,
        headers={
            "Content-Type": "application/json",
            "svix-id": msg_id,
            "svix-timestamp": ts,
            "svix-signature": sig,
        },
    )
    webhook_app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    assert response.json() == {"status": "ok"}
    assert existing_user.is_active is False


def test_user_created_sends_welcome_email(webhook_app, webhook_client, monkeypatch):
    """Brand-new user.created event triggers a welcome email."""
    import app.api.v1.routes.clerk_webhook as route

    fake_session = _FakeAsyncSession()

    async def override_db():
        yield fake_session

    async def fake_ensure(clerk_user_id, *, session, clerk_api=None):
        from app.models.models import User
        u = User(
            email="newbie@example.com",
            password_hash="clerk:placeholder",
            clerk_user_id=clerk_user_id,
            full_name="New Bie",
        )
        session.add(u)
        await session.commit()
        return u

    sent: list[dict] = []

    def fake_send(*, to, template, context, source):
        sent.append({"to": to, "template": template, "context": context, "source": source})
        return "msg_test"

    monkeypatch.setattr(route, "ensure_local_user_async", fake_ensure)
    monkeypatch.setattr(
        "app.services.notifications.channels.send_templated_email_best_effort",
        fake_send,
    )
    monkeypatch.setattr(settings, "FRONTEND_BASE_URL", "https://aidwiseai.com")
    webhook_app.dependency_overrides[get_db] = override_db

    payload = {
        "type": "user.created",
        "data": {
            "id": "user_welcome_001",
            "email_addresses": [{"id": "e1", "email_address": "newbie@example.com"}],
            "primary_email_address_id": "e1",
            "first_name": "New",
            "last_name": "Bie",
        },
    }
    msg_id, ts, sig = _sign_payload(TEST_SECRET, payload)
    body = json.dumps(payload)

    response = webhook_client.post(
        "/api/v1/webhooks/clerk",
        content=body,
        headers={
            "Content-Type": "application/json",
            "svix-id": msg_id,
            "svix-timestamp": ts,
            "svix-signature": sig,
        },
    )
    webhook_app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(sent) == 1
    assert sent[0]["to"] == "newbie@example.com"
    assert sent[0]["template"] == "welcome"
    assert sent[0]["source"] == "welcome"
    assert sent[0]["context"]["name"] == "New Bie"
    assert sent[0]["context"]["login_url"] == "https://aidwiseai.com/login"


def test_user_created_skips_welcome_when_user_already_exists(
    webhook_app, webhook_client, monkeypatch
):
    """An email-collision (linked) flow must NOT send a welcome."""
    from app.models.models import User
    import app.api.v1.routes.clerk_webhook as route

    fake_session = _FakeAsyncSession()
    existing = User(
        email="returning@example.com",
        password_hash="local:hash",
        clerk_user_id=None,
        full_name="Returning User",
    )
    fake_session._store.append(existing)

    async def override_db():
        yield fake_session

    async def fake_ensure(clerk_user_id, *, session, clerk_api=None):
        existing.clerk_user_id = clerk_user_id
        await session.commit()
        return existing

    sent: list = []

    def fake_send(**kwargs):
        sent.append(kwargs)
        return "msg_should_not_fire"

    monkeypatch.setattr(route, "ensure_local_user_async", fake_ensure)
    monkeypatch.setattr(
        "app.services.notifications.channels.send_templated_email_best_effort",
        fake_send,
    )
    webhook_app.dependency_overrides[get_db] = override_db

    payload = {
        "type": "user.created",
        "data": {
            "id": "user_linked_001",
            "email_addresses": [{"id": "e1", "email_address": "returning@example.com"}],
            "primary_email_address_id": "e1",
            "first_name": "Returning",
            "last_name": "User",
        },
    }
    msg_id, ts, sig = _sign_payload(TEST_SECRET, payload)
    body = json.dumps(payload)

    response = webhook_client.post(
        "/api/v1/webhooks/clerk",
        content=body,
        headers={
            "Content-Type": "application/json",
            "svix-id": msg_id,
            "svix-timestamp": ts,
            "svix-signature": sig,
        },
    )
    webhook_app.dependency_overrides.clear()

    assert response.status_code == 200
    assert sent == []
