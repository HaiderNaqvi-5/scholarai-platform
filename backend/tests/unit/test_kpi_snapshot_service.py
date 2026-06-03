import uuid
from typing import Any, cast

import pytest

from app.services.kpi_snapshot_service import KPISnapshotService



class _Result:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _ScalarRows:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _ScalarResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return _ScalarRows(self._rows)


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


class _FakeDeleteResult:
    def __init__(self, rowcount):
        self.rowcount = rowcount


class _FakePurgeSession:
    """Records each set-based DELETE; one execute per table, no get()/delete()."""

    def __init__(self, rowcounts):
        # rowcounts in call order: recommendation, document, interview
        self._rowcounts = list(rowcounts)
        self.executed = []
        self.flushed = 0

    async def execute(self, statement):
        self.executed.append(statement)
        rowcount = self._rowcounts[len(self.executed) - 1]
        return _FakeDeleteResult(rowcount)

    async def flush(self):
        self.flushed += 1
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
    from sqlalchemy.sql.dml import Delete

    from app.models import (
        DocumentKPISnapshot,
        InterviewKPISnapshot,
        RecommendationKPISnapshot,
    )

    fake_db = _FakePurgeSession(rowcounts=[2, 1, 0])
    service = KPISnapshotService(cast(Any, fake_db))

    deleted = await service.purge_snapshots_older_than(retention_days=30)

    assert deleted["recommendation_deleted"] == 2
    assert deleted["document_deleted"] == 1
    assert deleted["interview_deleted"] == 0
    assert deleted["total_deleted"] == 3

    # One set-based DELETE per table — NOT 1+2N per row.
    assert len(fake_db.executed) == 3
    assert all(isinstance(stmt, Delete) for stmt in fake_db.executed)
    assert fake_db.executed[0].table.name == RecommendationKPISnapshot.__tablename__
    assert fake_db.executed[1].table.name == DocumentKPISnapshot.__tablename__
    assert fake_db.executed[2].table.name == InterviewKPISnapshot.__tablename__
