import pytest
from fastapi.testclient import TestClient

from app.services.kpi_snapshot_service import KPISnapshotService
from app.core.database import get_db
from app.core.config import settings



class _RowsResult:
    def __init__(self, total: int, passed: int):
        self._total = total
        self._passed = passed

    def one_or_none(self):
        class _Row:
            def __init__(self, total: int, passed: int):
                self.total = total
                self.passed = passed

        return _Row(self._total, self._passed)


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
        total, passed = self.rows_by_call[self.execute_calls]
        self.execute_calls += 1
        return _RowsResult(total=total, passed=passed)


async def test_kpi_alert_messages_emits_alert_for_degraded_domain():
    fake_db = _FakeSession(
        rows_by_call=[
            (12, 10),
            (10, 4),
            (8, 6),
        ]
    )
    service = KPISnapshotService(fake_db)

    alerts = await service.alert_messages(
        lookback_days=14,
        min_snapshots_per_domain=5,
        recommendation_pass_rate_min=0.6,
        document_pass_rate_min=0.7,
        interview_pass_rate_min=0.6,
    )

    assert len(alerts) == 1
    assert alerts[0].domain == "document"
    assert alerts[0].severity == "warn"
    assert alerts[0].message.startswith("document KPI pass rate degraded")


async def test_kpi_alert_messages_skips_low_volume_domains():
    fake_db = _FakeSession(
        rows_by_call=[
            (3, 1),
            (2, 0),
            (1, 1),
        ]
    )
    service = KPISnapshotService(fake_db)

    alerts = await service.alert_messages(
        lookback_days=14,
        min_snapshots_per_domain=5,
        recommendation_pass_rate_min=0.6,
        document_pass_rate_min=0.7,
        interview_pass_rate_min=0.6,
    )

    assert alerts == []


def test_api_v1_health_never_returns_kpi_alerts_when_observability_enabled(app, monkeypatch):
    """P1-5 — GET /api/v1/health must never return KPI alert intelligence,
    even when KPI_OBSERVABILITY_ENABLED=True.

    The old code computed and returned kpi_alerts on this public, unauthenticated
    route whenever the flag was on, leaking recommendation/document/interview
    pass-rate signals.  The fix makes the route liveness-only: kpi_alerts is
    always [].  This test encodes the fix: it monkeypatches the flag to True,
    overrides get_db so the DB ping succeeds, and asserts kpi_alerts == [].
    """

    class _FakeDB:
        async def execute(self, _query):
            class _R:
                pass
            return _R()

    async def _override_get_db():
        yield _FakeDB()

    monkeypatch.setattr(settings, "KPI_OBSERVABILITY_ENABLED", True)
    app.dependency_overrides[get_db] = _override_get_db

    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["kpi_alerts"] == [], (
        "Public /api/v1/health must never expose KPI alert intelligence "
        "regardless of KPI_OBSERVABILITY_ENABLED (P1-5)"
    )
    assert payload["status"] == "healthy"
    assert payload["database"] == "ok"


async def test_health_endpoint_does_not_leak_kpi_alerts(app, client, monkeypatch):
    """S15 — Public /health probe must not surface KPI alert messages.

    KPI alerts can reveal volume + pass-rate signals to attackers. Admins
    consume the full KPI surface through the auth-gated
    /api/v1/analytics endpoint instead.
    """

    class _FakeDBSession:
        async def execute(self, _query):
            return None

    class _FakeSessionFactory:
        async def __aenter__(self):
            return _FakeDBSession()

        async def __aexit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr("app.main.async_session_factory", _FakeSessionFactory)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["database"] == "ok"
    assert payload["kpi_alerts"] == []
