"""
direction_models.py — Model Definitions and Baselines for Direction Forecasting

Implements:
1. Baseline classifiers:
   - MajorityClassBaseline
   - MomentumBaseline
   - PersistenceBaseline (Predicts STABLE)
2. Machine Learning Classifiers:
   - LogisticRegression
   - RandomForestClassifier
   - GradientBoostingClassifier
   - HistGradientBoostingClassifier
3. Multi-class metric extraction and decision-relevance evaluation.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, precision_score,
    recall_score, f1_score, confusion_matrix
)

# Target classes: -1 = DECREASE, 0 = STABLE, 1 = INCREASE
CLASSES = [-1, 0, 1]
CLASS_NAMES = ["DECREASE", "STABLE", "INCREASE"]


class MajorityClassBaseline:
    """Baseline predicting the most frequent class in training data."""
    def __init__(self):
        self.majority_class_ = 0

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.majority_class_ = y.mode()[0]
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.full(len(X), self.majority_class_)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        probs = np.zeros((len(X), len(CLASSES)))
        c_idx = CLASSES.index(self.majority_class_)
        probs[:, c_idx] = 1.0
        return probs


class PersistenceBaseline:
    """Baseline predicting price remains STABLE (0)."""
    def fit(self, X: pd.DataFrame, y: pd.Series):
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.zeros(len(X), dtype=int)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        probs = np.zeros((len(X), len(CLASSES)))
        probs[:, 1] = 1.0 # 0 is at index 1
        return probs


class MomentumBaseline:
    """Baseline using trailing 3-observation percentage momentum."""
    def __init__(self, threshold: float = 0.015):
        self.threshold = threshold

    def fit(self, X: pd.DataFrame, y: pd.Series):
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if "price_change_3_pct" in X.columns:
            mom = X["price_change_3_pct"].values
        elif "price_change_1_pct" in X.columns:
            mom = X["price_change_1_pct"].values
        else:
            return np.zeros(len(X), dtype=int)

        preds = np.zeros(len(X), dtype=int)
        preds[mom > self.threshold] = 1
        preds[mom < -self.threshold] = -1
        return preds

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        preds = self.predict(X)
        probs = np.full((len(X), len(CLASSES)), 0.1)
        for i, p in enumerate(preds):
            idx = CLASSES.index(p)
            probs[i, idx] = 0.8
        return probs


def get_model_pipeline(model_name: str, random_state: int = 42):
    """
    Instantiate model pipeline with appropriate pre-processing and class balancing.
    """
    m = model_name.lower()
    if m == "logistic_regression":
        return Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=random_state))
        ])
    elif m == "random_forest":
        return RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1
        )
    elif m == "gradient_boosting":
        return GradientBoostingClassifier(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.05,
            random_state=random_state
        )
    elif m == "hist_gradient_boosting":
        return HistGradientBoostingClassifier(
            max_iter=100,
            max_depth=5,
            class_weight="balanced",
            random_state=random_state
        )
    elif m == "majority_class":
        return MajorityClassBaseline()
    elif m == "persistence":
        return PersistenceBaseline()
    elif m == "momentum":
        return MomentumBaseline()
    else:
        raise ValueError(f"Unknown model: {model_name}")


def evaluate_classifier(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Dict[str, Any]:
    """
    Compute comprehensive classification metrics, confusion matrix,
    per-class statistics, and decision relevance.
    """
    preds = model.predict(X_test)

    # Probabilities if supported
    probs = None
    if hasattr(model, "predict_proba"):
        try:
            probs = model.predict_proba(X_test)
        except Exception:
            probs = None

    acc = accuracy_score(y_test, preds)
    b_acc = balanced_accuracy_score(y_test, preds)
    prec_macro = precision_score(y_test, preds, labels=CLASSES, average="macro", zero_division=0)
    rec_macro = recall_score(y_test, preds, labels=CLASSES, average="macro", zero_division=0)
    f1_macro = f1_score(y_test, preds, labels=CLASSES, average="macro", zero_division=0)
    f1_weighted = f1_score(y_test, preds, labels=CLASSES, average="weighted", zero_division=0)

    # Per-class metrics
    prec_per_class = precision_score(y_test, preds, labels=CLASSES, average=None, zero_division=0)
    rec_per_class = recall_score(y_test, preds, labels=CLASSES, average=None, zero_division=0)
    f1_per_class = f1_score(y_test, preds, labels=CLASSES, average=None, zero_division=0)

    # Confusion matrix
    cm = confusion_matrix(y_test, preds, labels=CLASSES)

    # Decision Relevance:
    # "WAIT" signal corresponds to predicting INCREASE (class 1)
    # "SELL" signal corresponds to predicting DECREASE (-1) or STABLE (0)
    wait_mask = (preds == 1)
    wait_precision = (y_test.values[wait_mask] == 1).mean() if wait_mask.sum() > 0 else 0.0

    sell_mask = (preds <= 0)
    sell_precision = (y_test.values[sell_mask] <= 0).mean() if sell_mask.sum() > 0 else 0.0

    return {
        "accuracy": round(float(acc), 4),
        "balanced_accuracy": round(float(b_acc), 4),
        "precision_macro": round(float(prec_macro), 4),
        "recall_macro": round(float(rec_macro), 4),
        "f1_macro": round(float(f1_macro), 4),
        "f1_weighted": round(float(f1_weighted), 4),
        "precision_decrease": round(float(prec_per_class[0]), 4),
        "precision_stable": round(float(prec_per_class[1]), 4),
        "precision_increase": round(float(prec_per_class[2]), 4),
        "recall_decrease": round(float(rec_per_class[0]), 4),
        "recall_stable": round(float(rec_per_class[1]), 4),
        "recall_increase": round(float(rec_per_class[2]), 4),
        "f1_decrease": round(float(f1_per_class[0]), 4),
        "f1_stable": round(float(f1_per_class[1]), 4),
        "f1_increase": round(float(f1_per_class[2]), 4),
        "wait_precision": round(float(wait_precision), 4),
        "sell_precision": round(float(sell_precision), 4),
        "confusion_matrix": cm,
        "predictions": preds,
        "probabilities": probs
    }
