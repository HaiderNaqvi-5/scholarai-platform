from app.services.recommendations.evaluation import (
    RecommendationEvaluationService,
    RecommendationMetricResult,
    RecommendationMetricThreshold,
)


def test_recommendation_evaluation_metrics_precision_recall_ndcg():
    service = RecommendationEvaluationService()

    metrics = service.evaluate(
        predicted_ids=["s1", "s2", "s3", "s4"],
        judged_relevance={"s1": 3, "s2": 1, "s3": 0, "s4": 2},
        k_values=[1, 3, 4],
    )

    by_k = {metric.k: metric for metric in metrics}
    assert by_k[1].precision_at_k == 1.0
    assert by_k[1].recall_at_k == 0.3333
    assert by_k[1].ndcg_at_k == 1.0
    assert by_k[1].mrr_at_k == 1.0

    assert by_k[3].precision_at_k == 0.6667
    assert by_k[3].recall_at_k == 0.6667
    assert by_k[3].ndcg_at_k > 0
    assert by_k[3].mrr_at_k == 1.0

    assert by_k[4].precision_at_k == 0.75
    assert by_k[4].recall_at_k == 1.0
    assert by_k[4].ndcg_at_k <= 1.0
    assert by_k[4].mrr_at_k == 1.0


def test_recommendation_evaluation_kpi_gates_thresholds_pass():
    service = RecommendationEvaluationService()
    metrics = [
        RecommendationMetricResult(k=3, precision_at_k=0.8, recall_at_k=0.7, ndcg_at_k=0.76, mrr_at_k=1.0),
    ]
    thresholds = [
        RecommendationMetricThreshold(
            k=3,
            precision_at_k_min=0.7,
            recall_at_k_min=0.6,
            ndcg_at_k_min=0.75,
        )
    ]

    results = service.evaluate_kpi_gates(metrics=metrics, thresholds=thresholds)

    assert len(results) == 1
    assert results[0].precision_at_k_pass is True
    assert results[0].recall_at_k_pass is True
    assert results[0].ndcg_at_k_pass is True
    assert results[0].ndcg_delta_pass is None
    assert results[0].all_passed is True


def test_recommendation_evaluation_kpi_gates_ndcg_delta_requires_baseline():
    service = RecommendationEvaluationService()
    metrics = [
        RecommendationMetricResult(k=5, precision_at_k=0.6, recall_at_k=0.6, ndcg_at_k=0.68, mrr_at_k=0.5),
    ]
    thresholds = [RecommendationMetricThreshold(k=5, ndcg_delta_min=0.02)]

    results_without_baseline = service.evaluate_kpi_gates(metrics=metrics, thresholds=thresholds)
    assert results_without_baseline[0].ndcg_delta_pass is False
    assert results_without_baseline[0].all_passed is False

    baseline_metrics = [
        RecommendationMetricResult(k=5, precision_at_k=0.55, recall_at_k=0.58, ndcg_at_k=0.65, mrr_at_k=0.5),
    ]
    results_with_baseline = service.evaluate_kpi_gates(
        metrics=metrics,
        thresholds=thresholds,
        baseline_metrics=baseline_metrics,
    )

    assert results_with_baseline[0].ndcg_delta_value == 0.03
    assert results_with_baseline[0].ndcg_delta_pass is True
    assert results_with_baseline[0].all_passed is True


def test_recommendation_evaluation_single_threshold_k_filters_results():
    service = RecommendationEvaluationService()
    metrics = [
        RecommendationMetricResult(k=1, precision_at_k=1.0, recall_at_k=0.4, ndcg_at_k=1.0, mrr_at_k=1.0),
        RecommendationMetricResult(k=3, precision_at_k=0.67, recall_at_k=0.67, ndcg_at_k=0.9, mrr_at_k=1.0),
    ]

    thresholds = [RecommendationMetricThreshold(k=1, precision_at_k_min=0.5)]
    results = service.evaluate_kpi_gates(metrics=metrics, thresholds=thresholds)

    assert len(results) == 1
    assert results[0].k == 1
    assert results[0].precision_at_k_pass is True


def test_recommendation_evaluation_metrics_mrr_returns_first_relevant_rank():
    service = RecommendationEvaluationService()
    metrics = service.evaluate(
        predicted_ids=["x1", "x2", "x3", "x4"],
        judged_relevance={"x1": 0, "x2": 0, "x3": 2, "x4": 1},
        k_values=[1, 3, 4],
    )
    by_k = {metric.k: metric for metric in metrics}
    assert by_k[1].mrr_at_k == 0.0
    assert by_k[3].mrr_at_k == 0.3333
    assert by_k[4].mrr_at_k == 0.3333
