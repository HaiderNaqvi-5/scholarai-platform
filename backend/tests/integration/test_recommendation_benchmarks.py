from datetime import datetime, timezone
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
    def __init__(self):
        self.recorded_snapshots = []

    def add(self, value):
        self.recorded_snapshots.append(value)
        return None

    async def flush(self):
        return None


def _benchmark_dataset_payload():
    return {
        "benchmark_id": "v01-core-rank-quality",
        "name": "v0.1 Core Recommendation Rank Quality",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": "test benchmark",
        "cases": [
            {
                "case_id": "case-1",
                "predicted_ids": ["s1", "s2", "s3"],
                "judged_relevance": {"s1": 3, "s2": 1, "s3": 0},
                "k_values": [1, 3],
            },
            {
                "case_id": "case-2",
                "predicted_ids": ["s9", "s8", "s7"],
                "judged_relevance": {"s9": 0, "s8": 1, "s7": 2},
                "k_values": [1, 3],
            },
        ],
    }


def _edge_benchmark_dataset_payload():
    return {
        "benchmark_id": "v01-edge-case-rank-quality",
        "name": "v0.1 Edge Case Recommendation Rank Quality",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": "edge benchmark",
        "cases": [
            {
                "case_id": "edge-1",
                "predicted_ids": ["e1", "e2", "e3"],
                "judged_relevance": {"e1": 0, "e2": 2, "e3": 1},
                "k_values": [1, 3],
            }
        ],
    }


def test_recommendation_benchmarks_list_and_evaluate(app, client):
    db = _NoOpDB()

    async def override_current_user():
        return _DummyCurrentUser()

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    import app.api.v1.routes.recommendations as recommendation_routes
    from app.schemas.recommendations import RecommendationBenchmarkDataset

    class FakeBenchmarkRegistry:
        def __init__(self):
            self.dataset = RecommendationBenchmarkDataset.model_validate(_benchmark_dataset_payload())
            self.edge_dataset = RecommendationBenchmarkDataset.model_validate(
                _edge_benchmark_dataset_payload()
            )

        def list_datasets(self):
            return [self.dataset, self.edge_dataset]

        def get_dataset(self, dataset_id: str):
            if dataset_id == self.dataset.benchmark_id:
                return self.dataset
            if dataset_id == self.edge_dataset.benchmark_id:
                return self.edge_dataset
            return None

    original_registry = recommendation_routes.RecommendationBenchmarkRegistry
    recommendation_routes.RecommendationBenchmarkRegistry = FakeBenchmarkRegistry
    try:
        list_response = client.get(
            "/api/v1/recommendations/benchmarks",
            headers={"Authorization": "Bearer fake"},
        )
        assert list_response.status_code == 200
        list_payload = list_response.json()
        assert list_payload["total"] == 2
        by_id = {item["benchmark_id"]: item for item in list_payload["items"]}
        assert "v01-core-rank-quality" in by_id
        assert "v01-edge-case-rank-quality" in by_id
        assert by_id["v01-core-rank-quality"]["case_count"] == 2
        assert by_id["v01-edge-case-rank-quality"]["case_count"] == 1
        assert "created_at" in by_id["v01-core-rank-quality"]
        assert "passed_count" in by_id["v01-core-rank-quality"]
        assert "failed_count" in by_id["v01-core-rank-quality"]

        evaluate_response = client.post(
            "/api/v1/recommendations/benchmarks/v01-core-rank-quality/evaluate",
            headers={"Authorization": "Bearer fake"},
        )
        assert evaluate_response.status_code == 200
        evaluate_payload = evaluate_response.json()
        assert evaluate_payload["summary"]["benchmark_id"] == "v01-core-rank-quality"
        assert len(evaluate_payload["cases"]) == 2
        assert len(evaluate_payload["aggregate"]["gate_pass_rates"]) >= 1
        assert evaluate_payload["summary"]["passed_count"] + evaluate_payload["summary"]["failed_count"] == 2
        assert all("mrr_at_k" in metric for case in evaluate_payload["cases"] for metric in case["metrics"])
        assert len(db.recorded_snapshots) == 1
        assert db.recorded_snapshots[0].policy_version == "reco.kpi.v1"

        not_found_response = client.post(
            "/api/v1/recommendations/benchmarks/unknown/evaluate",
            headers={"Authorization": "Bearer fake"},
        )
        assert not_found_response.status_code == 404
    finally:
        recommendation_routes.RecommendationBenchmarkRegistry = original_registry
        app.dependency_overrides.clear()
