from app.core.config import settings
from app.services.kpi_policy import (
    get_document_quality_policy_version,
    get_document_quality_thresholds,
    get_interview_progression_policy_version,
    get_interview_progression_thresholds,
    get_recommendation_default_thresholds,
    get_recommendation_kpi_policy_version,
)


def test_kpi_policy_versions_are_exposed():
    assert get_recommendation_kpi_policy_version() == "reco.kpi.v1"
    assert get_document_quality_policy_version() == "document.quality.v1"
    assert get_interview_progression_policy_version() == "interview.progression.v1"


def test_recommendation_default_thresholds_have_expected_k_values():
    thresholds = get_recommendation_default_thresholds()
    assert [threshold.k for threshold in thresholds] == [1, 3, 5, 10]
    assert all(threshold.precision_at_k_min == 0.4 for threshold in thresholds)
    assert all(threshold.recall_at_k_min == 0.2 for threshold in thresholds)
    assert all(threshold.ndcg_at_k_min == 0.45 for threshold in thresholds)


def test_document_and_interview_thresholds_are_config_backed():
    document_thresholds = get_document_quality_thresholds()
    assert document_thresholds.min_citation_coverage_ratio == 0.8
    assert document_thresholds.max_caution_note_count == 1
    assert document_thresholds.min_grounded_partition_count == 3
    assert document_thresholds.min_actionable_guidance_count == 2

    interview_thresholds = get_interview_progression_thresholds()
    assert interview_thresholds.min_answered_count == 2
    assert interview_thresholds.min_average_score == 3.0
    assert interview_thresholds.min_follow_up_actionability_ratio == 0.7
    assert interview_thresholds.min_adaptive_guidance_coverage == 0.7


def test_recommendation_default_thresholds_follow_settings(monkeypatch):
    monkeypatch.setattr(settings, "RECOMMENDATION_KPI_DEFAULT_K_VALUES", "2,4,4,invalid,0")
    monkeypatch.setattr(settings, "RECOMMENDATION_KPI_PRECISION_MIN", 0.51)
    monkeypatch.setattr(settings, "RECOMMENDATION_KPI_RECALL_MIN", 0.31)
    monkeypatch.setattr(settings, "RECOMMENDATION_KPI_NDCG_MIN", 0.61)
    monkeypatch.setattr(settings, "RECOMMENDATION_KPI_NDCG_DELTA_MIN", 0.05)

    thresholds = get_recommendation_default_thresholds()

    assert [threshold.k for threshold in thresholds] == [2, 4]
    assert all(threshold.precision_at_k_min == 0.51 for threshold in thresholds)
    assert all(threshold.recall_at_k_min == 0.31 for threshold in thresholds)
    assert all(threshold.ndcg_at_k_min == 0.61 for threshold in thresholds)
    assert all(threshold.ndcg_delta_min == 0.05 for threshold in thresholds)
