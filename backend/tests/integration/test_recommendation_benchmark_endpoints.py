from uuid import uuid4

from app.core.dependencies import get_current_user
from app.models import UserRole


class _DummyCurrentUser:
    def __init__(self):
        self.id = uuid4()
        self.role = UserRole.ADMIN
        self._token_capabilities = {
            "recommendation.evaluate",
            "admin.audit.read",
            "owner.system.read",
        }


def test_recommendation_benchmark_list_requires_auth(client):
    response = client.get("/api/v1/recommendations/benchmarks")

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_recommendation_benchmark_endpoints_authorized(app, client):
    async def override_current_user():
        return _DummyCurrentUser()

    app.dependency_overrides[get_current_user] = override_current_user

    list_response = client.get(
        "/api/v1/recommendations/benchmarks",
        headers={"Authorization": "Bearer fake"},
    )
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["total"] >= 1
    first = list_payload["items"][0]
    assert first["dataset_id"] == "v0_1_judged_core_set"
    assert first["policy_version"] == "reco.kpi.v1"

    eval_response = client.post(
        "/api/v1/recommendations/benchmarks/v0_1_judged_core_set/evaluate",
        headers={"Authorization": "Bearer fake"},
    )
    app.dependency_overrides.clear()

    assert eval_response.status_code == 200
    eval_payload = eval_response.json()
    assert eval_payload["dataset_id"] == "v0_1_judged_core_set"
    assert eval_payload["policy_version"] == "reco.kpi.v1"
    assert eval_payload["aggregate"]["case_count"] >= 1
    assert 0 <= eval_payload["aggregate"]["pass_rate"] <= 1
    assert len(eval_payload["case_results"]) >= 1


def test_recommendation_benchmark_not_found_returns_404(app, client):
    async def override_current_user():
        return _DummyCurrentUser()

    app.dependency_overrides[get_current_user] = override_current_user
    response = client.post(
        "/api/v1/recommendations/benchmarks/not-a-real-dataset/evaluate",
        headers={"Authorization": "Bearer fake"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert "not found" in response.json()["error"]["message"].lower()
