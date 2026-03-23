from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import UserRole
from uuid import uuid4


class _DummyCurrentUser:
    def __init__(self):
        self.id = uuid4()
        self.role = UserRole.ADMIN
        self._token_capabilities = {
            "recommendation.evaluate",
            "admin.audit.read",
            "owner.system.read",
        }


class _NoOpDB:
    def add(self, _value):
        return None

    async def flush(self):
        return None


def test_recommendation_evaluate_returns_policy_version_when_authorized(app, client):
    async def override_current_user():
        return _DummyCurrentUser()

    async def override_db():
        yield _NoOpDB()

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    response = client.post(
        "/api/v1/recommendations/evaluate",
        json={
            "predicted_ids": ["a", "b", "c"],
            "judged_relevance": {"a": 3, "b": 1, "c": 0},
            "k_values": [1, 3],
        },
        headers={"Authorization": "Bearer fake"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["policy_version"] == "reco.kpi.v1"
    assert payload["kpi_passed"] is not None
