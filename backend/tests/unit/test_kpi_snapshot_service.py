import uuid
from typing import Any, cast

import pytest

from app.services.kpi_snapshot_service import KPISnapshotService


pytestmark = pytest.mark.asyncio


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeSession:
    def __init__(self, rows_by_call):
        self.rows_by_call = rows_by_call
        self.added = []
        self.execute_calls = 0

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        return None

    async def execute(self, _query):
        rows = self.rows_by_call[self.execute_calls]
        self.execute_calls += 1
        return _Result(rows)


class _BulkDeleteResult:
    def __init__(self, rowcount: int):
        self.rowcount = rowcount


class _FakeCleanupSession:
    def __init__(self):
        self.execute_calls = 0

    async def execute(self, _query):
        self.execute_calls += 1
        if self.execute_calls == 1:
            return _BulkDeleteResult(2)
        if self.execute_calls == 2:
            return _BulkDeleteResult(1)
        if self.execute_calls == 3:
            return _BulkDeleteResult(0)
        return _BulkDeleteResult(0)

    async def flush(self):
        return None


async def test_kpi_snapshot_service_records_snapshots():
    fake_db = _FakeSession(rows_by_call=[[]])
    service = KPISnapshotService(cast(Any, fake_db))

    await service.record_recommendation_snapshot(
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
        policy_version="reco.kpi.v1",
        kpi_passed=True,
        metrics_payload=[{"k": 1, "precision_at_k": 1.0}],
        gates_payload=[{"k": 1, "all_passed": True}],
    )

    assert len(fake_db.added) == 1
    assert fake_db.added[0].policy_version == "reco.kpi.v1"
    assert fake_db.added[0].kpi_passed is True


async def test_kpi_snapshot_service_builds_trend_items():
    fake_db = _FakeSession(
        rows_by_call=[
            [("reco.kpi.v1", 10, 7)],
            [("document.quality.v1", 8, 6)],
            [("interview.progression.v1", 5, 2)],
        ]
    )
    service = KPISnapshotService(cast(Any, fake_db))

    recommendation = await service.recommendation_trends()
    documents = await service.document_trends()
    interviews = await service.interview_trends()

    assert recommendation[0].metric_domain == "recommendation"
    assert recommendation[0].policy_version == "reco.kpi.v1"
    assert recommendation[0].failed_snapshots == 3
    assert recommendation[0].pass_rate == 0.7

    assert documents[0].metric_domain == "document"
    assert documents[0].failed_snapshots == 2
    assert documents[0].pass_rate == 0.75

    assert interviews[0].metric_domain == "interview"
    assert interviews[0].failed_snapshots == 3
    assert interviews[0].pass_rate == 0.4


async def test_kpi_snapshot_service_purges_old_snapshots():
    fake_db = _FakeCleanupSession()
    service = KPISnapshotService(cast(Any, fake_db))

    deleted = await service.purge_snapshots_older_than(retention_days=30)

    assert deleted["recommendation_deleted"] == 2
    assert deleted["document_deleted"] == 1
    assert deleted["interview_deleted"] == 0
    assert deleted["total_deleted"] == 3
    assert fake_db.execute_calls == 3
