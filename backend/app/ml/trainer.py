import argparse
import os
import json

import mlflow
import xgboost as xgb
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def train_model(data_path: str, model_output_path: str):
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    features = ["gpa", "ielts_score", "research_score", "volunteer_score", "program_match_score"]
    X = df[features]
    y = df["success"]

    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp)

    mlflow.xgboost.autolog()

    with mlflow.start_run():
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dval = xgb.DMatrix(X_val, label=y_val)
        dtest = xgb.DMatrix(X_test, label=y_test)

        params = {
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "max_depth": 3,
            "learning_rate": 0.1,
            "random_state": 42
        }

        evals = [(dtrain, "train"), (dval, "val")]
        model = xgb.train(params, dtrain, num_boost_round=100, evals=evals, early_stopping_rounds=10, verbose_eval=False)

        # Evaluate on test set
        preds_prob = model.predict(dtest)
        preds = (preds_prob > 0.5).astype(int)
        
        acc = accuracy_score(y_test, preds)
        prec = precision_score(y_test, preds)
        rec = recall_score(y_test, preds)
        f1 = f1_score(y_test, preds)
        
        metrics = {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1
        }
        mlflow.log_metrics(metrics)

        print(f"Test Metrics: {metrics}")

        os.makedirs(os.path.dirname(os.path.abspath(model_output_path)), exist_ok=True)
        model.save_model(model_output_path)
        print(f"Model saved to {model_output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train XGBoost Model")
    parser.add_argument("--data", type=str, default="data/synthetic_v1.csv", help="Input CSV path")
    parser.add_argument("--output", type=str, default="models/xgboost_model.json", help="Output model path")
    args = parser.parse_args()
    
    train_model(args.data, args.output)
