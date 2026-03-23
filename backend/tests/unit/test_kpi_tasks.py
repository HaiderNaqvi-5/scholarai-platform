from __future__ import annotations

import pytest

pytest.importorskip("celery")

from app.tasks import kpi_tasks


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


def test_run_kpi_snapshot_retention_cleanup_when_enabled(monkeypatch):
    fake_session = FakeSession()
    captured = {}

    class FakeKPISnapshotService:
        def __init__(self, db):
            captured["db"] = db

        async def purge_snapshots_older_than(self, *, retention_days):
            captured["retention_days"] = retention_days
            return {
                "recommendation_deleted": 2,
                "document_deleted": 1,
                "interview_deleted": 0,
                "total_deleted": 3,
            }

    monkeypatch.setattr(
        kpi_tasks,
        "async_session_factory",
        lambda: FakeSessionContext(fake_session),
    )
    monkeypatch.setattr(kpi_tasks, "KPISnapshotService", FakeKPISnapshotService)
    monkeypatch.setattr(kpi_tasks.settings, "KPI_SNAPSHOT_RETENTION_ENABLED", True)
    monkeypatch.setattr(kpi_tasks.settings, "KPI_SNAPSHOT_RETENTION_DAYS", 45)

    result = kpi_tasks.run_kpi_snapshot_retention_cleanup()

    assert captured["db"] is fake_session
    assert captured["retention_days"] == 45
    assert result["enabled"] is True
    assert result["retention_days"] == 45
    assert result["total_deleted"] == 3
    assert fake_session.commits == 1


def test_run_kpi_snapshot_retention_cleanup_when_disabled(monkeypatch):
    monkeypatch.setattr(kpi_tasks.settings, "KPI_SNAPSHOT_RETENTION_ENABLED", False)
    monkeypatch.setattr(kpi_tasks.settings, "KPI_SNAPSHOT_RETENTION_DAYS", 60)

    result = kpi_tasks.run_kpi_snapshot_retention_cleanup()

    assert result["enabled"] is False
    assert result["retention_days"] == 60
    assert result["recommendation_deleted"] == 0
    assert result["document_deleted"] == 0
    assert result["interview_deleted"] == 0
    assert result["total_deleted"] == 0
