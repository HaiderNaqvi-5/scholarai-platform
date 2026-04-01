from __future__ import annotations

import json

import pytest

from app.services.recommendations.benchmark_registry import (
    RecommendationBenchmarkRegistry,
    RecommendationBenchmarkRegistryError,
)


def _valid_dataset_payload() -> dict:
    return {
        "dataset_id": "sample_benchmark",
        "version": "2026-04-01",
        "title": "Sample benchmark",
        "description": "Sample benchmark data",
        "frozen_at": "2026-04-01T00:00:00Z",
        "k_values": [1, 3, 5],
        "thresholds": [
            {"k": 1, "precision_at_k_min": 0.4, "recall_at_k_min": 0.2, "ndcg_at_k_min": 0.45}
        ],
        "baseline_metrics": [
            {"k": 1, "precision_at_k": 0.5, "recall_at_k": 0.3, "ndcg_at_k": 0.55}
        ],
        "cases": [
            {
                "case_id": "case-a",
                "profile_label": "Profile A",
                "predicted_ids": ["a", "b", "c"],
                "judged_relevance": {"a": 3, "b": 1, "c": 0},
            }
        ],
    }


def test_registry_loads_datasets_from_directory(tmp_path):
    dataset_path = tmp_path / "sample_benchmark.json"
    dataset_path.write_text(json.dumps(_valid_dataset_payload()), encoding="utf-8")

    registry = RecommendationBenchmarkRegistry(dataset_dir=tmp_path)
    datasets = registry.list_datasets()

    assert len(datasets) == 1
    assert datasets[0].dataset_id == "sample_benchmark"
    assert datasets[0].cases[0].case_id == "case-a"


def test_registry_rejects_invalid_json_file(tmp_path):
    broken_path = tmp_path / "broken.json"
    broken_path.write_text("{not-valid-json", encoding="utf-8")

    registry = RecommendationBenchmarkRegistry(dataset_dir=tmp_path)
    with pytest.raises(RecommendationBenchmarkRegistryError, match="Invalid JSON"):
        registry.list_datasets()


def test_registry_rejects_invalid_dataset_schema(tmp_path):
    bad_payload = _valid_dataset_payload()
    bad_payload["cases"][0]["judged_relevance"] = {"a": -1}
    bad_path = tmp_path / "invalid_schema.json"
    bad_path.write_text(json.dumps(bad_payload), encoding="utf-8")

    registry = RecommendationBenchmarkRegistry(dataset_dir=tmp_path)
    with pytest.raises(RecommendationBenchmarkRegistryError, match="Invalid benchmark dataset schema"):
        registry.list_datasets()
