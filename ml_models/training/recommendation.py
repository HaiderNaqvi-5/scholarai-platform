"""
ScholarAI Recommendation Engine
XGBoost-based scholarship matching with SHAP explainability
"""
import numpy as np
import pandas as pd
import xgboost as xgb
import shap
import joblib
from pathlib import Path


MODEL_DIR = Path(__file__).parent.parent / "trained"


def build_feature_vector(student: dict, scholarship: dict) -> np.ndarray:
    """Convert student + scholarship profiles into a feature vector for the model."""
    features = [
        student.get("gpa", 0) / student.get("gpa_scale", 4.0),
        student.get("research_publications", 0),
        student.get("research_experience_months", 0),
        student.get("leadership_roles", 0),
        student.get("volunteer_hours", 0),
        student.get("language_test_score", 0),
        1 if student.get("field_of_study") in (scholarship.get("field_of_study") or []) else 0,
        1 if student.get("country_of_origin") != scholarship.get("country") else 0,
        1 if student.get("degree_level") in (scholarship.get("degree_levels") or []) else 0,
        scholarship.get("min_gpa", 0),
        scholarship.get("funding_amount_usd", 0) / 100000,
    ]
    return np.array(features).reshape(1, -1)


FEATURE_NAMES = [
    "normalized_gpa", "research_pubs", "research_exp_months",
    "leadership_roles", "volunteer_hours", "language_score",
    "field_match", "international", "degree_match",
    "scholarship_min_gpa", "funding_normalized",
]


def train_model(X: np.ndarray, y: np.ndarray) -> xgb.XGBClassifier:
    """Train XGBoost model on scholarship match data."""
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(X, y)
    return model


def save_model(model, filename="recommendation_model.pkl"):
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_DIR / filename)


def load_model(filename="recommendation_model.pkl"):
    return joblib.load(MODEL_DIR / filename)


def predict_match(model, features: np.ndarray) -> dict:
    """Predict match score and success probability."""
    match_prob = model.predict_proba(features)[0][1]
    return {
        "match_score": round(match_prob * 100, 1),
        "success_probability": round(match_prob * 100 * 0.6, 1),  # conservative estimate
    }


def explain_prediction(model, features: np.ndarray) -> list:
    """Generate SHAP explanations for a prediction."""
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(features)

    contributions = []
    for i, name in enumerate(FEATURE_NAMES):
        contributions.append({
            "feature": name,
            "contribution": round(float(shap_values[0][i]) * 100, 1),
        })

    contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)
    return contributions
