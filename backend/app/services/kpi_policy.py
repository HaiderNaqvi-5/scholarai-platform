from __future__ import annotations

from app.core.config import settings
from app.schemas.documents import DocumentQualityThresholds
from app.schemas.interviews import InterviewProgressionThresholds
from app.services.recommendations.evaluation import RecommendationMetricThreshold


def get_recommendation_kpi_policy_version() -> str:
    return settings.RECOMMENDATION_KPI_POLICY_VERSION


def get_recommendation_default_thresholds() -> list[RecommendationMetricThreshold]:
    k_values = _parse_k_values(settings.RECOMMENDATION_KPI_DEFAULT_K_VALUES)
    return [
        RecommendationMetricThreshold(
            k=k,
            precision_at_k_min=settings.RECOMMENDATION_KPI_PRECISION_MIN,
            recall_at_k_min=settings.RECOMMENDATION_KPI_RECALL_MIN,
            ndcg_at_k_min=settings.RECOMMENDATION_KPI_NDCG_MIN,
            ndcg_delta_min=settings.RECOMMENDATION_KPI_NDCG_DELTA_MIN,
        )
        for k in k_values
    ]


def get_document_quality_policy_version() -> str:
    return settings.DOCUMENT_QUALITY_POLICY_VERSION


def get_document_quality_thresholds() -> DocumentQualityThresholds:
    return DocumentQualityThresholds(
        min_citation_coverage_ratio=settings.DOCUMENT_QUALITY_MIN_CITATION_COVERAGE_RATIO,
        max_caution_note_count=settings.DOCUMENT_QUALITY_MAX_CAUTION_NOTE_COUNT,
        min_retrieved_guidance_count=settings.DOCUMENT_QUALITY_MIN_RETRIEVED_GUIDANCE_COUNT,
        min_generated_guidance_count=settings.DOCUMENT_QUALITY_MIN_GENERATED_GUIDANCE_COUNT,
    )


def get_interview_progression_policy_version() -> str:
    return settings.INTERVIEW_PROGRESSION_POLICY_VERSION


def get_interview_progression_thresholds() -> InterviewProgressionThresholds:
    return InterviewProgressionThresholds(
        min_answered_count=settings.INTERVIEW_PROGRESSION_MIN_ANSWERED_COUNT,
        min_average_score=settings.INTERVIEW_PROGRESSION_MIN_AVERAGE_SCORE,
        min_score_delta=settings.INTERVIEW_PROGRESSION_MIN_SCORE_DELTA,
        max_needs_focus_ratio=settings.INTERVIEW_PROGRESSION_MAX_NEEDS_FOCUS_RATIO,
    )


def _parse_k_values(raw_k_values: str) -> list[int]:
    parsed: list[int] = []
    for chunk in raw_k_values.split(","):
        value = chunk.strip()
        if not value:
            continue
        try:
            number = int(value)
        except ValueError:
            continue
        if number >= 1:
            parsed.append(number)

    if not parsed:
        return [1, 3, 5, 10]

    return sorted(set(parsed))
