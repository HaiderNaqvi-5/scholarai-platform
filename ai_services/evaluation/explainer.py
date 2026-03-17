import json
from typing import Dict, Any

import numpy as np
import pandas as pd
import shap
import lime
import lime.lime_tabular
import xgboost as xgb


class ShapExplainer:
    def __init__(self, model_path: str):
        self.model = xgb.Booster()
        self.model.load_model(model_path)
        self.explainer = shap.TreeExplainer(self.model)

    def explain_prediction(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Generate feature contributions for a single prediction using SHAP.
        """
        df = pd.DataFrame([features])
        dmatrix = xgb.DMatrix(df)
        prob = float(self.model.predict(dmatrix)[0])
        shap_values = self.explainer.shap_values(df)
        base_value = float(self.explainer.expected_value)
        if isinstance(base_value, np.ndarray):
             base_value = base_value[0]
        
        contributions = {}
        for idx, col in enumerate(df.columns):
            val = float(shap_values[0][idx])
            pct_shift = val * 10
            sign = "+" if pct_shift >= 0 else ""
            contributions[col] = f"{sign}{pct_shift:.1f}%"
            
        return {
            "prediction_probability": round(prob, 3),
            "base_value": round(base_value, 3),
            "contributions": contributions,
            "raw_shap": {col: float(shap_values[0][idx]) for idx, col in enumerate(df.columns)}
        }


class LimeExplainer:
    def __init__(self, model_path: str, training_data_path: str = None):
        self.model = xgb.Booster()
        self.model.load_model(model_path)
        self.feature_names = ["gpa", "ielts_score", "research_score", "volunteer_score", "program_match_score"]
        
        # Load or mock training data for LIME initialization
        if training_data_path:
            training_data = pd.read_csv(training_data_path)
        else:
            # Fallback to normal-ish distribution for dev/mocking
            training_data = pd.DataFrame(
                np.random.normal(0.5, 0.2, (500, 5)), 
                columns=self.feature_names
            )
            
        self.explainer = lime.lime_tabular.LimeTabularExplainer(
            training_data.values,
            feature_names=self.feature_names,
            class_names=['Low Fit', 'High Fit'],
            mode='regression'
        )

    def _predict_fn(self, x):
        # LIME expects a function that takes a numpy array and returns predictions
        df = pd.DataFrame(x, columns=self.feature_names)
        dmatrix = xgb.DMatrix(df)
        return self.model.predict(dmatrix)

    def explain_prediction(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Generate feature contributions for a single prediction using LIME.
        """
        df = pd.DataFrame([features])
        # exp.as_list() returns tuples of (feature_name_range, contribution)
        exp = self.explainer.explain_instance(
            df.values[0], 
            self._predict_fn, 
            num_features=5
        )
        
        return {
            "prediction": float(self._predict_fn(df.values)[0]),
            "contributions": {name: float(val) for name, val in exp.as_list()},
            "intercept": float(exp.intercept) if hasattr(exp, 'intercept') else 0
        }
