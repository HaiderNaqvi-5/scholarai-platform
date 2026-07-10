from uuid import uuid4

from app.core.database import get_db
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


class _NoOpDB:
    def add(self, _value):
        return None

    async def flush(self):
        return None


def test_recommendation_benchmark_list_requires_auth(client):
    response = client.get("/api/v1/recommendations/benchmarks")

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_recommendation_benchmark_endpoints_authorized(app, client):
    async def override_current_user():
        return _DummyCurrentUser()

    async def override_db():
        yield _NoOpDB()

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db
    try:
        list_response = client.get(
            "/api/v1/recommendations/benchmarks",
            headers={"Authorization": "Bearer fake"},
        )
        assert list_response.status_code == 200
        list_payload = list_response.json()
        assert list_payload["total"] >= 1
        dataset_ids = {item["dataset_id"] for item in list_payload["items"]}
        assert "v0_1_judged_core_set" in dataset_ids
        core_item = next(item for item in list_payload["items"] if item["dataset_id"] == "v0_1_judged_core_set")
        assert core_item["policy_version"] == "reco.kpi.v1"

        eval_response = client.post(
            "/api/v1/recommendations/benchmarks/v0_1_judged_core_set/evaluate",
            headers={"Authorization": "Bearer fake"},
        )

        assert eval_response.status_code == 200
        eval_payload = eval_response.json()
        assert eval_payload["dataset_id"] == "v0_1_judged_core_set"
        assert eval_payload["policy_version"] == "reco.kpi.v1"
        assert eval_payload["aggregate"]["case_count"] >= 1
        assert 0 <= eval_payload["aggregate"]["pass_rate"] <= 1
        assert len(eval_payload["case_results"]) >= 1
    finally:
        app.dependency_overrides.clear()


def test_recommendation_benchmark_not_found_returns_404(app, client):
    async def override_current_user():
        return _DummyCurrentUser()

    async def override_db():
        yield _NoOpDB()

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db
    try:
        response = client.post(
            "/api/v1/recommendations/benchmarks/not-a-real-dataset/evaluate",
            headers={"Authorization": "Bearer fake"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["error"]["message"].lower()
    finally:
        app.dependency_overrides.clear()


def test_recommendation_benchmark_vacuous_thresholds_do_not_inflate_pass_rate(app, client, monkeypatch):
    """P2-18 followup: a dataset whose thresholds are all-None (nothing
    configured to check) must not report cases as passed -- pass_count/
    pass_rate must reflect 0 checked-and-passed cases, and each case's
    kpi_passed must be None (unknown), never True."""
    from app.schemas.recommendations import RecommendationBenchmarkDataset

    vacuous_dataset = RecommendationBenchmarkDataset.model_validate(
        {
            "dataset_id": "vacuous-thresholds",
            "version": "v1",
            "title": "Vacuous thresholds fixture",
            "k_values": [5],
            "thresholds": [{"k": 5}],
            "baseline_metrics": [],
            "cases": [
                {
                    "case_id": "case-1",
                    "predicted_ids": ["a", "b", "c"],
                    "judged_relevance": {"a": 1, "b": 0, "c": 1},
                },
                {
                    "case_id": "case-2",
                    "predicted_ids": ["x", "y"],
                    "judged_relevance": {"x": 1, "y": 1},
                },
            ],
        }
    )

    class _FakeRegistry:
        def __init__(self, *args, **kwargs):
            pass

        def get_dataset(self, dataset_id):
            assert dataset_id == "vacuous-thresholds"
            return vacuous_dataset

    monkeypatch.setattr(
        "app.api.v1.routes.recommendations.RecommendationBenchmarkRegistry",
        _FakeRegistry,
    )

    async def override_current_user():
        return _DummyCurrentUser()

    async def override_db():
        yield _NoOpDB()

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db
    try:
        response = client.post(
            "/api/v1/recommendations/benchmarks/vacuous-thresholds/evaluate",
            headers={"Authorization": "Bearer fake"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["aggregate"]["case_count"] == 2
        assert payload["aggregate"]["pass_count"] == 0
        assert payload["aggregate"]["pass_rate"] == 0.0
        assert len(payload["case_results"]) == 2
        for case in payload["case_results"]:
            assert case["kpi_gates"] == []
            assert case["kpi_passed"] is None
    finally:
        app.dependency_overrides.clear()
