from app.services.recommendations.evaluation import RecommendationEvaluationService


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

    assert by_k[3].precision_at_k == 0.6667
    assert by_k[3].recall_at_k == 0.6667
    assert by_k[3].ndcg_at_k > 0

    assert by_k[4].precision_at_k == 0.75
    assert by_k[4].recall_at_k == 1.0
    assert by_k[4].ndcg_at_k <= 1.0
