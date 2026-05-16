"""Unit tests for the priority scholarship alerts Celery task (PRD §0.6).

Uses a fake async session (queued query results) so the task logic — plan
gating, tracker exclusion, country targeting — is covered without a live DB.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

import app.tasks.alert_tasks as alert_tasks
from app.services.notifications import channels as notification_channels


# ---------------------------------------------------------------------------
# Fake async session
# ---------------------------------------------------------------------------


class _FakeScalars:
    def __init__(self, rows):
        self._rows = list(rows)

    def all(self):
        return self._rows


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return _FakeScalars(self._rows)

    def all(self):
        # Bulk-tuple queries (e.g. select(user_id, scholarship_id)) bypass
        # `.scalars()` and call `.all()` directly on the Result.
        return list(self._rows)


class _FakeSession:
    """Pops queued result-lists in execute() call order.

    Also tracks `db.add(...)` calls so tests can assert ledger rows were
    appended (e.g. WhatsApp burn-cap accounting).
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
        alert_tasks, "async_session_factory", lambda: _FakeSession(results)
    )


# ---------------------------------------------------------------------------
# Fixtures / builders
# ---------------------------------------------------------------------------


def _scholarship(country="GB", days_out=3):
    return SimpleNamespace(
        id=uuid.uuid4(),
        title=f"Test Scholarship {country}",
        country_code=country,
        deadline_at=datetime.now(timezone.utc) + timedelta(days=days_out),
    )


def _user(plan="elite", *, target_countries=("GB",), phone="+923001234567"):
    profile = SimpleNamespace(
        target_countries=list(target_countries),
        target_country_code=None,
        phone_e164=phone,
        whatsapp_e164=phone,
    )
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="student@example.com",
        is_active=True,
        plan=plan,
        plan_currency="PKR",
        student_profile=profile,
    )


# ---------------------------------------------------------------------------
# Channel-matrix invariants (Q1 retier: WhatsApp-only premium, no SMS)
# ---------------------------------------------------------------------------


def test_send_sms_function_removed():
    """send_sms must be deleted, not just deprecated."""
    from app.services.notifications import channels

    assert not hasattr(channels, "send_sms")


def test_plan_channels_matrix_q1_retier():
    """PLAN_CHANNELS now encodes email + WhatsApp (no SMS) for premium tiers."""
    assert notification_channels.PLAN_CHANNELS["free"] == ("email",)
    assert notification_channels.PLAN_CHANNELS["pro"] == ("email",)
    assert notification_channels.PLAN_CHANNELS["elite"] == ("email", "whatsapp")
    assert notification_channels.PLAN_CHANNELS["institution"] == ("email", "whatsapp")
    # Defensive: ensure no "sms" channel survives anywhere in the matrix.
    for plan, chs in notification_channels.PLAN_CHANNELS.items():
        assert "sms" not in chs, f"plan={plan} still references sms"


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_scholarships_due_short_circuits(monkeypatch):
    _patch_session(monkeypatch, [[]])  # scholarships query empty
    result = await alert_tasks._run_priority_scholarship_alerts_async()
    assert result == {"scholarships_due": 0, "users_notified": 0, "alerts_sent": 0}


@pytest.mark.asyncio
async def test_free_user_filtered_at_sql_level(monkeypatch):
    # Free users are excluded by the SQL plan filter — the user-loading query
    # returns empty, so the task short-circuits without iterating users.
    scholarship = _scholarship("GB")
    _patch_session(
        monkeypatch,
        [
            [scholarship],  # scholarships due
            [],             # users — free was filtered out by .where(User.plan.in_(paid))
        ],
    )
    result = await alert_tasks._run_priority_scholarship_alerts_async()
    assert result["scholarships_due"] == 1
    assert result["users_notified"] == 0
    assert result["alerts_sent"] == 0


@pytest.mark.asyncio
async def test_pro_user_gets_email_only(monkeypatch):
    scholarship = _scholarship("GB")
    pro_user = _user("pro")
    # Order: scholarships → paid users → bulk tracker rows
    _patch_session(monkeypatch, [[scholarship], [pro_user], []])
    result = await alert_tasks._run_priority_scholarship_alerts_async()
    assert result["users_notified"] == 1
    assert result["alerts_sent"] == 1  # email only


@pytest.mark.asyncio
async def test_elite_user_gets_email_and_whatsapp(monkeypatch):
    """Q1 retier: Elite = email + WhatsApp (SMS removed)."""
    scholarship = _scholarship("GB")
    elite_user = _user("elite")
    _patch_session(monkeypatch, [[scholarship], [elite_user], []])
    result = await alert_tasks._run_priority_scholarship_alerts_async()
    assert result["users_notified"] == 1
    assert result["alerts_sent"] == 2  # email + whatsapp (no sms)


@pytest.mark.asyncio
async def test_already_tracked_scholarship_is_excluded(monkeypatch):
    scholarship = _scholarship("GB")
    elite_user = _user("elite")
    # Bulk tracker rows are now tuples (user_id, scholarship_id).
    _patch_session(
        monkeypatch,
        [[scholarship], [elite_user], [(elite_user.id, scholarship.id)]],
    )
    result = await alert_tasks._run_priority_scholarship_alerts_async()
    assert result["users_notified"] == 0


@pytest.mark.asyncio
async def test_country_mismatch_is_excluded(monkeypatch):
    scholarship = _scholarship("US")  # user targets GB only
    elite_user = _user("elite", target_countries=("GB",))
    _patch_session(monkeypatch, [[scholarship], [elite_user], []])
    result = await alert_tasks._run_priority_scholarship_alerts_async()
    assert result["users_notified"] == 0


# ---------------------------------------------------------------------------
# Burn-cap ledger integration: WhatsApp sends must write usage_ledger rows.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_whatsapp_records_usage_ledger_row():
    """send_whatsapp(db, user, msg) must append a 'whatsapp' UsageLedger row."""
    from app.models import UsageLedger

    db = _FakeSession([])
    user = _user("elite")
    ok = await notification_channels.send_whatsapp(db, user, "msg")
    assert ok is True
    ledger_rows = [row for row in db.added if isinstance(row, UsageLedger)]
    assert ledger_rows, "send_whatsapp must record a UsageLedger row"
    assert ledger_rows[0].kind == "whatsapp"
    assert ledger_rows[0].user_id == user.id


@pytest.mark.asyncio
async def test_priority_alerts_records_whatsapp_ledger(monkeypatch):
    """Running the alerts task for an Elite user must record WhatsApp in the ledger."""
    from app.models import UsageLedger

    scholarship = _scholarship("GB")
    elite_user = _user("elite")
    fake = _FakeSession([[scholarship], [elite_user], []])
    monkeypatch.setattr(alert_tasks, "async_session_factory", lambda: fake)

    await alert_tasks._run_priority_scholarship_alerts_async()

    ledger_rows = [
        row
        for row in fake.added
        if isinstance(row, UsageLedger) and row.kind == "whatsapp"
    ]
    assert ledger_rows, "Elite priority alert must record a WhatsApp ledger row"
    assert ledger_rows[0].user_id == elite_user.id
