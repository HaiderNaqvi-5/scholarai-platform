from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RecommendationMetricResult:
    k: int
    precision_at_k: float
    recall_at_k: float
    ndcg_at_k: float


@dataclass(frozen=True)
class RecommendationMetricThreshold:
    k: int
    precision_at_k_min: float | None = None
    recall_at_k_min: float | None = None
    ndcg_at_k_min: float | None = None
    ndcg_delta_min: float | None = None


@dataclass(frozen=True)
class RecommendationKPIGateResult:
    k: int
    precision_at_k_pass: bool | None
    recall_at_k_pass: bool | None
    ndcg_at_k_pass: bool | None
    ndcg_delta_pass: bool | None
    ndcg_delta_value: float | None
    all_passed: bool


class RecommendationEvaluationService:
    def evaluate(
        self,
        *,
        predicted_ids: list[str],
        judged_relevance: dict[str, int],
        k_values: list[int],
    ) -> list[RecommendationMetricResult]:
        relevant_total = sum(1 for score in judged_relevance.values() if score > 0)
        normalized_k_values = self._normalize_k_values(k_values, len(predicted_ids))

        return [
            RecommendationMetricResult(
                k=k,
                precision_at_k=self._precision_at_k(predicted_ids, judged_relevance, k),
                recall_at_k=self._recall_at_k(predicted_ids, judged_relevance, k, relevant_total),
                ndcg_at_k=self._ndcg_at_k(predicted_ids, judged_relevance, k),
            )
            for k in normalized_k_values
        ]

    def evaluate_kpi_gates(
        self,
        *,
        metrics: list[RecommendationMetricResult],
        thresholds: list[RecommendationMetricThreshold],
        baseline_metrics: list[RecommendationMetricResult] | None = None,
    ) -> list[RecommendationKPIGateResult]:
        metric_by_k = {metric.k: metric for metric in metrics}
        baseline_by_k = {metric.k: metric for metric in (baseline_metrics or [])}
        results: list[RecommendationKPIGateResult] = []

        for threshold in thresholds:
            metric = metric_by_k.get(threshold.k)
            if metric is None:
                continue

            precision_pass = self._gte_or_none(metric.precision_at_k, threshold.precision_at_k_min)
            recall_pass = self._gte_or_none(metric.recall_at_k, threshold.recall_at_k_min)
            ndcg_pass = self._gte_or_none(metric.ndcg_at_k, threshold.ndcg_at_k_min)

            baseline_metric = baseline_by_k.get(threshold.k)
            ndcg_delta_value = None
            ndcg_delta_pass = None
            if threshold.ndcg_delta_min is not None:
                if baseline_metric is not None:
                    ndcg_delta_value = round(metric.ndcg_at_k - baseline_metric.ndcg_at_k, 4)
                    ndcg_delta_pass = ndcg_delta_value >= threshold.ndcg_delta_min
                else:
                    ndcg_delta_pass = False

            checks = [
                value
                for value in (precision_pass, recall_pass, ndcg_pass, ndcg_delta_pass)
                if value is not None
            ]
            all_passed = all(checks) if checks else True

            results.append(
                RecommendationKPIGateResult(
                    k=threshold.k,
                    precision_at_k_pass=precision_pass,
                    recall_at_k_pass=recall_pass,
                    ndcg_at_k_pass=ndcg_pass,
                    ndcg_delta_pass=ndcg_delta_pass,
                    ndcg_delta_value=ndcg_delta_value,
                    all_passed=all_passed,
                )
            )

        return results

    def aggregate_metrics(
        self,
        metrics_by_case: list[list[RecommendationMetricResult]],
    ) -> list[RecommendationMetricResult]:
        """Compute average metrics across all cases, grouped by k."""
        if not metrics_by_case:
            return []

        sums: dict[int, dict[str, float]] = {}
        counts: dict[int, int] = {}
        for case_metrics in metrics_by_case:
            for metric in case_metrics:
                if metric.k not in sums:
                    sums[metric.k] = {"precision_at_k": 0.0, "recall_at_k": 0.0, "ndcg_at_k": 0.0}
                    counts[metric.k] = 0
                sums[metric.k]["precision_at_k"] += metric.precision_at_k
                sums[metric.k]["recall_at_k"] += metric.recall_at_k
                sums[metric.k]["ndcg_at_k"] += metric.ndcg_at_k
                counts[metric.k] += 1

        return [
            RecommendationMetricResult(
                k=k,
                precision_at_k=round(sums[k]["precision_at_k"] / counts[k], 4),
                recall_at_k=round(sums[k]["recall_at_k"] / counts[k], 4),
                ndcg_at_k=round(sums[k]["ndcg_at_k"] / counts[k], 4),
            )
            for k in sorted(sums)
        ]

    def _gte_or_none(self, actual: float, minimum: float | None) -> bool | None:
        if minimum is None:
            return None
        return actual >= minimum

    def _normalize_k_values(self, k_values: list[int], prediction_count: int) -> list[int]:
        if not k_values:
            return [1, 3, 5, 10]
        max_k = max(prediction_count, 1)
        unique = sorted({min(max(k, 1), max_k) for k in k_values})
        return unique

    def _precision_at_k(
        self,
        predicted_ids: list[str],
        judged_relevance: dict[str, int],
        k: int,
    ) -> float:
        top_k = predicted_ids[:k]
        if not top_k:
            return 0.0
        hits = sum(1 for scholarship_id in top_k if judged_relevance.get(scholarship_id, 0) > 0)
        return round(hits / len(top_k), 4)

    def _recall_at_k(
        self,
        predicted_ids: list[str],
        judged_relevance: dict[str, int],
        k: int,
        relevant_total: int,
    ) -> float:
        if relevant_total == 0:
            return 0.0
        top_k = predicted_ids[:k]
        hits = sum(1 for scholarship_id in top_k if judged_relevance.get(scholarship_id, 0) > 0)
        return round(hits / relevant_total, 4)

    def _ndcg_at_k(
        self,
        predicted_ids: list[str],
        judged_relevance: dict[str, int],
        k: int,
    ) -> float:
        top_k = predicted_ids[:k]
        if not top_k:
            return 0.0

        dcg = self._dcg([judged_relevance.get(scholarship_id, 0) for scholarship_id in top_k])
        ideal_relevances = sorted(judged_relevance.values(), reverse=True)[:k]
        idcg = self._dcg(ideal_relevances)
        if idcg == 0:
            return 0.0
        return round(dcg / idcg, 4)

    def _dcg(self, relevances: list[int]) -> float:
        score = 0.0
        for index, relevance in enumerate(relevances):
            if relevance <= 0:
                continue
            score += (2**relevance - 1) / math.log2(index + 2)
        return score
