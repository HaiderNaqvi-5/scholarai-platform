+
"""
ScholarAI Model Evaluation
Metrics: Precision@K, NDCG, accuracy, ROC-AUC
"""
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    ndcg_score,
)


def evaluate_model(y_true, y_pred, y_prob=None):
    """Evaluate recommendation model with standard metrics."""
    results = {
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_true, y_pred, zero_division=0), 4),
    }

    if y_prob is not None:
        results["roc_auc"] = round(roc_auc_score(y_true, y_prob), 4)

    return results


def precision_at_k(y_true, y_scores, k=10):
    """Precision@K for top-K recommendations."""
    top_k_indices = np.argsort(y_scores)[-k:]
    relevant = sum(y_true[i] for i in top_k_indices)
    return round(relevant / k, 4)
