from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RecommendationMetricResult:
    k: int
    precision_at_k: float
    recall_at_k: float
    ndcg_at_k: float


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
