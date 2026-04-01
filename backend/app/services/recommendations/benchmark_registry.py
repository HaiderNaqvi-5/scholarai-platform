from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.schemas.recommendations import RecommendationBenchmarkDataset

BENCHMARK_DATASET_DIR = Path(__file__).resolve().parents[2] / "data" / "recommendation_benchmarks"


class RecommendationBenchmarkRegistryError(RuntimeError):
    pass


class RecommendationBenchmarkRegistry:
    def __init__(self, dataset_dir: Path | None = None) -> None:
        self.dataset_dir = dataset_dir or BENCHMARK_DATASET_DIR

    def list_datasets(self) -> list[RecommendationBenchmarkDataset]:
        if not self.dataset_dir.exists():
            raise RecommendationBenchmarkRegistryError(
                f"Benchmark dataset directory is missing: {self.dataset_dir}"
            )

        datasets: list[RecommendationBenchmarkDataset] = []
        for file_path in sorted(self.dataset_dir.glob("*.json")):
            datasets.append(self._load_dataset_file(file_path))

        if not datasets:
            raise RecommendationBenchmarkRegistryError(
                f"No benchmark dataset files found in {self.dataset_dir}"
            )

        return datasets

    def get_dataset(self, dataset_id: str) -> RecommendationBenchmarkDataset:
        normalized_id = dataset_id.strip().lower()
        for dataset in self.list_datasets():
            if dataset.dataset_id.strip().lower() == normalized_id:
                return dataset

        raise RecommendationBenchmarkRegistryError(
            f"Benchmark dataset not found: {dataset_id}"
        )

    def _load_dataset_file(self, file_path: Path) -> RecommendationBenchmarkDataset:
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RecommendationBenchmarkRegistryError(
                f"Invalid JSON in benchmark dataset file: {file_path.name}"
            ) from exc

        try:
            return RecommendationBenchmarkDataset.model_validate(payload)
        except ValidationError as exc:
            raise RecommendationBenchmarkRegistryError(
                f"Invalid benchmark dataset schema in {file_path.name}: {exc}"
            ) from exc
