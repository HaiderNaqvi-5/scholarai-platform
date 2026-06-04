from __future__ import annotations

import pytest

pytest.importorskip("celery")

from app.tasks import usage_ledger_tasks


class FakeSession:
    def __init__(self):
        self.commits = 0

    async def commit(self):
        self.commits += 1


class FakeSessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


def test_run_usage_ledger_rollup_when_enabled(monkeypatch):
    fake_session = FakeSession()
    captured = {}

    class FakeUsageLedgerMaintenanceService:
        def __init__(self, db):
            captured["db"] = db

        async def rollup_and_prune(self, *, retention_months):
            captured["retention_months"] = retention_months
            return {"periods_rolled_up": 2, "rows_pruned": 17}

    monkeypatch.setattr(
        usage_ledger_tasks,
        "async_session_factory",
        lambda: FakeSessionContext(fake_session),
    )
    monkeypatch.setattr(
        usage_ledger_tasks,
        "UsageLedgerMaintenanceService",
        FakeUsageLedgerMaintenanceService,
    )
    monkeypatch.setattr(
        usage_ledger_tasks.settings, "USAGE_LEDGER_ROLLUP_ENABLED", True
    )
    monkeypatch.setattr(
        usage_ledger_tasks.settings, "USAGE_LEDGER_RETENTION_MONTHS", 13
    )

    result = usage_ledger_tasks.run_usage_ledger_rollup()

    assert captured["db"] is fake_session
    assert captured["retention_months"] == 13
    assert result["enabled"] is True
    assert result["retention_months"] == 13
    assert result["rows_pruned"] == 17
    assert result["periods_rolled_up"] == 2
    assert fake_session.commits == 1


def test_run_usage_ledger_rollup_when_disabled(monkeypatch):
    monkeypatch.setattr(
        usage_ledger_tasks.settings, "USAGE_LEDGER_ROLLUP_ENABLED", False
    )
    monkeypatch.setattr(
        usage_ledger_tasks.settings, "USAGE_LEDGER_RETENTION_MONTHS", 13
    )

    result = usage_ledger_tasks.run_usage_ledger_rollup()

    assert result["enabled"] is False
    assert result["retention_months"] == 13
    assert result["rows_pruned"] == 0
    assert result["periods_rolled_up"] == 0
