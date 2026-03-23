from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import UserRole


class _DummyCurrentUser:
    def __init__(self):
        self.role = UserRole.ADMIN
        self._token_capabilities = {
            "admin.audit.read",
            "owner.system.read",
        }


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class _RowsResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeAnalyticsDB:
    def __init__(self):
        self.scalar_values = [10, 6, 2, 2, 20, 11, 5, 8, 7, 4, 1]
        self.row_values = [
            [("reco.kpi.v1", 6, 4)],
            [("document.quality.v1", 5, 3)],
            [("interview.progression.v1", 4, 2)],
        ]
        self.scalar_idx = 0
        self.rows_idx = 0

    async def execute(self, query):
        query_text = str(query)
        if "GROUP BY" in query_text:
            rows = self.row_values[self.rows_idx]
            self.rows_idx += 1
            return _RowsResult(rows)

        value = self.scalar_values[self.scalar_idx]
        self.scalar_idx += 1
        return _ScalarResult(value)


def test_analytics_includes_kpi_trends(app, client):
    async def override_current_user():
        return _DummyCurrentUser()

    async def override_db():
        yield _FakeAnalyticsDB()

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    response = client.get(
        "/api/v1/analytics",
        headers={"Authorization": "Bearer fake"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert "kpi_trends" in payload
    assert len(payload["kpi_trends"]) == 3
    assert payload["kpi_trends"][0]["metric_domain"] == "recommendation"
