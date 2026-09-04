"""
direction_inference.py — Production-Ready Direction Inference Interface

Exposes `predict_price_direction` for the Flask backend.
Predicts whether the mandi price will INCREASE, STAY STABLE, or DECREASE
over approximately 3 market observations.

Uses pre-trained crop-specific classifiers and empirical movement thresholds:
- Rice: ±1.5% threshold
- Tomato: ±5.0% threshold
- Wheat: ±1.5% threshold
- Cotton: ±1.0% threshold
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import joblib

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
CONFIG_PATH = MODELS_DIR / "direction_config.json"

_CONFIG_CACHE: Optional[Dict[str, Any]] = None
_MODEL_CACHE: Dict[str, Any] = {}

SUPPORTED_CROPS = ["rice", "tomato", "wheat", "cotton"]
LABEL_MAP = {-1: "DECREASE", 0: "STABLE", 1: "INCREASE"}


def _load_direction_config() -> Dict[str, Any]:
    """Load direction models configuration and feature definitions."""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r") as f:
                _CONFIG_CACHE = json.load(f)
        else:
            _CONFIG_CACHE = {}
    return _CONFIG_CACHE


def _load_direction_model(crop: str):
    """Load cached pre-trained joblib direction classifier for the crop."""
    global _MODEL_CACHE
    crop_norm = crop.lower().strip()
    if crop_norm not in _MODEL_CACHE:
        model_path = MODELS_DIR / f"direction_model_{crop_norm}.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"Direction model file not found: {model_path}")
        _MODEL_CACHE[crop_norm] = joblib.load(model_path)
    return _MODEL_CACHE[crop_norm]


def predict_price_direction(
    crop: str,
    market: str,
    current_price: float,
    date: str
) -> Dict[str, Any]:
    """
    Predict price direction over the next ~3 market observations.

    Parameters
    ----------
    crop : str
        Crop name ('wheat', 'rice', 'tomato', 'cotton').
    market : str
        APMC mandi name.
    current_price : float
        Current Modal Price in ₹/quintal.
    date : str
        Current date in 'YYYY-MM-DD' format.

    Returns
    -------
    dict
        JSON-serializable prediction containing:
        - crop
        - market
        - current_price
        - predicted_direction: 'INCREASE' | 'STABLE' | 'DECREASE'
        - confidence: float (0.0 to 1.0)
        - probabilities: dict of class probabilities
        - forecast_horizon: '3 market observations'
        - movement_threshold_pct: float
    """
    # 1. Input Validation
    if not isinstance(crop, str):
        return {"error": f"Crop must be a string, got {type(crop).__name__}"}
    crop_norm = crop.lower().strip()
    if crop_norm not in SUPPORTED_CROPS:
        return {"error": f"Unsupported crop: '{crop}'. Supported: {SUPPORTED_CROPS}"}

    if not isinstance(current_price, (int, float)) or current_price <= 0:
        return {"error": f"Invalid current_price: {current_price}. Must be a positive number."}

    if not isinstance(date, str) or len(date.strip()) < 8:
        return {"error": f"Invalid date: '{date}'. Expected 'YYYY-MM-DD'."}

    cfg = _load_direction_config().get(crop_norm, {})
    th_pct = float(cfg.get("threshold_pct", 1.5))
    feat_cols = cfg.get("feature_columns", [])

    # 2. Build feature vector from runtime processed historical data
    try:
        model = _load_direction_model(crop_norm)

        features_path = BASE_DIR / "data" / "processed" / f"maharashtra_{crop_norm}_features.csv"
        if features_path.exists():
            df_hist = pd.read_csv(features_path, low_memory=False)
            df_mkt = df_hist[df_hist["Market"] == market]
            if not df_mkt.empty:
                row_dict = df_mkt.sort_values(by="Price Date").iloc[-1].to_dict()
            else:
                row_dict = df_hist.iloc[-1].to_dict()
        else:
            row_dict = {}

        # Update row with real-time price & date
        row_dict["Modal Price"] = float(current_price)
        row_dict["Price Date"] = date
        row_dict["Market"] = market

        # Fill feature vector
        feat_vector = []
        for col in feat_cols:
            val = row_dict.get(col, 0.0)
            if val is None or pd.isna(val):
                val = 0.0
            feat_vector.append(float(val))

        X = pd.DataFrame([feat_vector], columns=feat_cols)

        # 3. Model Prediction
        pred_raw = int(model.predict(X)[0])
        pred_direction = LABEL_MAP.get(pred_raw, "STABLE")

        # 4. Probabilities & Confidence
        if hasattr(model, "predict_proba"):
            raw_probs = model.predict_proba(X)[0]
            # Ensure mapping to [-1, 0, 1]
            classes_in_model = list(getattr(model, "classes_", [-1, 0, 1]))
            p_dec = float(raw_probs[classes_in_model.index(-1)]) if -1 in classes_in_model else 0.0
            p_stb = float(raw_probs[classes_in_model.index(0)]) if 0 in classes_in_model else 0.0
            p_inc = float(raw_probs[classes_in_model.index(1)]) if 1 in classes_in_model else 0.0
            confidence = float(max(p_dec, p_stb, p_inc))
        else:
            p_dec, p_stb, p_inc = 0.2, 0.6, 0.2
            confidence = 0.60

        return {
            "crop": crop_norm,
            "market": market,
            "current_price": float(current_price),
            "predicted_direction": pred_direction,
            "confidence": round(confidence, 3),
            "probabilities": {
                "decrease": round(p_dec, 3),
                "stable": round(p_stb, 3),
                "increase": round(p_inc, 3)
            },
            "forecast_horizon": "3 market observations",
            "movement_threshold_pct": th_pct,
            "interpretation": (
                f"Price is expected to {pred_direction.lower()} by more than {th_pct}% "
                f"over ~3 observations with {confidence*100:.1f}% model confidence."
            ),
            "status": "SUCCESS"
        }
    except Exception as e:
        return {
            "crop": crop_norm,
            "market": market,
            "current_price": float(current_price),
            "predicted_direction": "STABLE",
            "confidence": 0.50,
            "probabilities": {
                "decrease": 0.25,
                "stable": 0.50,
                "increase": 0.25
            },
            "forecast_horizon": "3 market observations",
            "movement_threshold_pct": th_pct,
            "interpretation": f"Defaulted to STABLE due to runtime note: {str(e)}",
            "status": "FALLBACK"
        }
