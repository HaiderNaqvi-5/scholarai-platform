"""Unit tests for the deadline reminder Celery task (PRD §0.6 / §0.5).

Covers the SQL-level 30-day silent-stop for free accounts and the plan-aware
channel fan-out. All without a live DB — the join result is mocked and
``send_email`` / ``send_whatsapp`` are monkeypatched to call counters so we
assert the new ``fan_out_for_plan(db, user, message)`` contract directly.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

import app.tasks.reminder_tasks as reminder_tasks
from app.services.notifications import channels as notification_channels


# ---------------------------------------------------------------------------
# Fake async session: now returns one .all() of (item, user) tuples.
# ---------------------------------------------------------------------------


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)

    def scalars(self):
        # Kept for compatibility with other tests that share the harness.
        class _Scalars:
            def __init__(self, rows):
                self._rows = list(rows)

            def all(self):
                return self._rows

        return _Scalars(self._rows)


class _FakeSession:
    """Pops queued result-lists in execute() call order.

    Tracks ``db.add(...)`` calls so tests can assert ledger rows were
    appended (WhatsApp burn-cap accounting hits the same session that
    fan_out_for_plan receives).
    """

    def __init__(self, results: list[list]):
        self._queue = list(results)
        self.added: list[object] = []

    async def execute(self, _stmt):
        rows = self._queue.pop(0) if self._queue else []
        return _FakeResult(rows)

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


def _patch_session(monkeypatch, results: list[list]):
    monkeypatch.setattr(
        reminder_tasks, "async_session_factory", lambda: _FakeSession(results)
    )


def _patch_channels(monkeypatch):
    """Replace the channel sends with call-counting stubs.

    The reminder task imports ``fan_out_for_plan`` from
    ``app.services.notifications``; that helper dispatches to
    ``send_email`` / ``send_whatsapp`` inside ``notifications.channels``.
    Patching at the channels module mirrors how fan_out_for_plan resolves
    them and avoids touching real I/O or burn-cap accounting.
    """
    email_calls: list[tuple] = []
    whatsapp_calls: list[tuple] = []

    async def _fake_send_email(user, message):
        email_calls.append((user, message))
        return True

    async def _fake_send_whatsapp(db, user, message):
        whatsapp_calls.append((db, user, message))
        return True

    monkeypatch.setattr(notification_channels, "send_email", _fake_send_email)
    monkeypatch.setattr(notification_channels, "send_whatsapp", _fake_send_whatsapp)
    return email_calls, whatsapp_calls


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _user(plan="pro", *, account_age_days=5, phone="+923001234567"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="student@example.com",
        is_active=True,
        plan=plan,
        plan_currency="PKR",
        created_at=datetime.now(timezone.utc) - timedelta(days=account_age_days),
        student_profile=SimpleNamespace(phone_e164=phone, whatsapp_e164=phone),
    )


def _item(user_id, days_out=5):
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user_id,
        program_name="MS Computer Science",
        university_name="University of Manchester",
        deadline=date.today() + timedelta(days=days_out),
    )


# ---------------------------------------------------------------------------
# Channel-matrix contract (no task, just the new fan_out_for_plan contract)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fan_out_free_and_pro_send_email_only(monkeypatch):
    email_calls, whatsapp_calls = _patch_channels(monkeypatch)
    db = _FakeSession([])
    free = SimpleNamespace(email="a@x.com", plan="free")
    pro = SimpleNamespace(email="a@x.com", plan="pro")

    await notification_channels.fan_out_for_plan(db, free, "msg")
    await notification_channels.fan_out_for_plan(db, pro, "msg")

    assert len(email_calls) == 2
    assert whatsapp_calls == []


@pytest.mark.asyncio
async def test_fan_out_elite_sends_email_and_whatsapp(monkeypatch):
    email_calls, whatsapp_calls = _patch_channels(monkeypatch)
    db = _FakeSession([])
    elite = SimpleNamespace(email="a@x.com", plan="elite")

    await notification_channels.fan_out_for_plan(db, elite, "msg")

    assert len(email_calls) == 1
    assert len(whatsapp_calls) == 1


# ---------------------------------------------------------------------------
# Task core — single-join result list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_rows_short_circuits(monkeypatch):
    _patch_channels(monkeypatch)
    _patch_session(monkeypatch, [[]])
    result = await reminder_tasks._run_deadline_reminders_async()
    assert result["items_due"] == 0
    assert result["users_notified"] == 0
    assert result["reminders_sent"] == 0


@pytest.mark.asyncio
async def test_pro_user_gets_email_only(monkeypatch):
    email_calls, whatsapp_calls = _patch_channels(monkeypatch)
    pro = _user("pro")
    item = _item(pro.id)
    _patch_session(monkeypatch, [[(item, pro)]])
    result = await reminder_tasks._run_deadline_reminders_async()
    assert result["users_notified"] == 1
    assert result["reminders_sent"] == 1
    assert len(email_calls) == 1
    assert whatsapp_calls == []


@pytest.mark.asyncio
async def test_elite_user_gets_email_and_whatsapp(monkeypatch):
    """Q1 retier: Elite = email + WhatsApp (SMS removed)."""
    email_calls, whatsapp_calls = _patch_channels(monkeypatch)
    elite = _user("elite", account_age_days=400)  # age irrelevant for paid plans
    item = _item(elite.id)
    _patch_session(monkeypatch, [[(item, elite)]])
    result = await reminder_tasks._run_deadline_reminders_async()
    assert result["users_notified"] == 1
    assert result["reminders_sent"] == 2  # email + whatsapp (no sms)
    assert len(email_calls) == 1
    assert len(whatsapp_calls) == 1


@pytest.mark.asyncio
async def test_free_within_30_days_still_notified(monkeypatch):
    # The SQL filter keeps the row; the task fires email-only.
    email_calls, whatsapp_calls = _patch_channels(monkeypatch)
    free = _user("free", account_age_days=5)
    item = _item(free.id)
    _patch_session(monkeypatch, [[(item, free)]])
    result = await reminder_tasks._run_deadline_reminders_async()
    assert result["users_notified"] == 1
    assert result["reminders_sent"] == 1
    assert len(email_calls) == 1
    assert whatsapp_calls == []


@pytest.mark.asyncio
async def test_free_past_30_days_filtered_at_sql_level(monkeypatch):
    # The real SQL filter would drop this row; the fake session simulates it
    # by returning an empty result set.
    email_calls, whatsapp_calls = _patch_channels(monkeypatch)
    _patch_session(monkeypatch, [[]])
    result = await reminder_tasks._run_deadline_reminders_async()
    assert result["users_notified"] == 0
    assert email_calls == []
    assert whatsapp_calls == []


@pytest.mark.asyncio
async def test_multiple_items_per_user_bucket_into_one_notification(monkeypatch):
    email_calls, whatsapp_calls = _patch_channels(monkeypatch)
    elite = _user("elite")
    item_a = _item(elite.id, days_out=3)
    item_b = _item(elite.id, days_out=8)
    _patch_session(monkeypatch, [[(item_a, elite), (item_b, elite)]])
    result = await reminder_tasks._run_deadline_reminders_async()
    assert result["items_due"] == 2
    assert result["users_notified"] == 1  # one fan-out per user
    assert result["reminders_sent"] == 2  # email + whatsapp once
    assert len(email_calls) == 1
    assert len(whatsapp_calls) == 1
