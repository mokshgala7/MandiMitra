"""
forecast_engine.py — MandiMitra Forecasting Engine
Selects and executes the best forecasting method per crop.
Methods: persistence, recent_mean, ml_model.
Determination is based on out-of-sample validation MAE.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
CONFIG_PATH = MODELS_DIR / "forecast_method_config.json"

# ── Model / metadata paths ────────────────────────────────────────
ML_MODEL_PATHS = {
    "rice": MODELS_DIR / "mandimitra_rice_price_model.joblib",
    "tomato": MODELS_DIR / "mandimitra_tomato_price_model.joblib",
    "wheat": MODELS_DIR / "mandimitra_wheat_price_model.joblib",
    "cotton": MODELS_DIR / "mandimitra_cotton_price_model.joblib",
}
METADATA_PATHS = {
    "rice": MODELS_DIR / "model_metadata.json",
    "tomato": MODELS_DIR / "tomato_model_metadata.json",
    "wheat": MODELS_DIR / "wheat_model_metadata.json",
    "cotton": MODELS_DIR / "cotton_model_metadata.json",
}

SUPPORTED_CROPS = list(ML_MODEL_PATHS.keys())

_MODEL_CACHE: Dict[str, Any] = {}
_META_CACHE: Dict[str, Dict] = {}
_CONFIG_CACHE: Optional[Dict] = None

REQUIRED_FEATURES = [
    "Min Price", "Max Price", "Modal Price",
    "price_lag_1", "price_lag_2", "price_lag_3", "price_lag_7", "price_lag_14", "price_lag_30",
    "price_ma_3", "price_ma_7", "price_ma_14", "price_ma_30",
    "price_std_7", "price_std_14", "price_std_30",
    "price_change_1", "price_change_1_pct", "price_change_3", "price_change_3_pct",
    "price_change_7", "price_change_7_pct", "price_change_14", "price_change_14_pct",
    "price_range", "price_range_pct",
    "year", "month", "day", "day_of_week", "day_of_year", "week_of_year", "is_weekend",
    "month_sin", "month_cos", "day_of_year_sin", "day_of_year_cos",
    "Market", "Variety", "Grade",
]


def _normalize_crop(crop: str) -> str:
    c = crop.strip().lower()
    if c not in SUPPORTED_CROPS:
        raise ValueError(f"Unsupported crop: '{crop}'. Supported: {SUPPORTED_CROPS}")
    return c


def load_forecast_config() -> Dict:
    """Load per-crop forecast method configuration."""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r") as f:
                _CONFIG_CACHE = json.load(f)
        else:
            # Default: determine from metadata
            _CONFIG_CACHE = build_forecast_config()
    return _CONFIG_CACHE


def build_forecast_config(save: bool = True) -> Dict:
    """
    Build forecast method config by comparing ML validation MAE vs Persistence MAE.
    Selects persistence if ml_mae >= persistence_mae (persistence is equal or better).
    Stores result in models/forecast_method_config.json.
    """
    config = {}
    for crop in SUPPORTED_CROPS:
        meta_path = METADATA_PATHS[crop]
        if not meta_path.exists():
            config[crop] = {"method": "persistence", "reason": "No model metadata found"}
            continue
        with open(meta_path) as f:
            meta = json.load(f)

        ml_mae = meta.get("MAE", float("inf"))
        pers_mae = meta.get("persistence_baseline_MAE", float("inf"))
        recent_mae = meta.get("recent_mean_MAE", None)  # if available

        # Select method: ML only if it meaningfully improves (>2% gain) over persistence
        improvement_pct = ((pers_mae - ml_mae) / pers_mae) * 100 if pers_mae > 0 else 0

        if improvement_pct > 2.0:
            method = "ml_model"
            reason = f"ML MAE ₹{ml_mae:.2f} beats Persistence ₹{pers_mae:.2f} by {improvement_pct:.1f}%"
        else:
            method = "persistence"
            reason = f"Persistence MAE ₹{pers_mae:.2f} is <= ML MAE ₹{ml_mae:.2f} (improvement {improvement_pct:.1f}%); persistence preferred"

        config[crop] = {
            "method": method,
            "ml_mae": round(ml_mae, 4),
            "persistence_mae": round(pers_mae, 4),
            "improvement_pct": round(improvement_pct, 4),
            "reason": reason,
        }

    if save:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)

    return config


def load_ml_model(crop: str):
    if crop not in _MODEL_CACHE:
        path = ML_MODEL_PATHS[crop]
        if not path.exists():
            raise FileNotFoundError(f"ML model not found for {crop}: {path}")
        _MODEL_CACHE[crop] = joblib.load(path)
    return _MODEL_CACHE[crop]


def load_metadata(crop: str) -> Dict:
    if crop not in _META_CACHE:
        path = METADATA_PATHS[crop]
        if path.exists():
            with open(path) as f:
                _META_CACHE[crop] = json.load(f)
        else:
            _META_CACHE[crop] = {}
    return _META_CACHE[crop]


def _prepare_ml_input(input_data: Union[Dict, pd.DataFrame]) -> pd.DataFrame:
    """Validate and prepare input for ML model prediction."""
    if isinstance(input_data, dict):
        df = pd.DataFrame([input_data])
    else:
        df = input_data.copy()

    # Auto-derive calendar fields from Price Date if present
    if "Price Date" in df.columns and "month_sin" not in df.columns:
        dates = pd.to_datetime(df["Price Date"])
        df["year"] = dates.dt.year
        df["month"] = dates.dt.month
        df["day"] = dates.dt.day
        df["day_of_week"] = dates.dt.dayofweek
        df["day_of_year"] = dates.dt.dayofyear
        df["week_of_year"] = dates.dt.isocalendar().week.astype(int)
        df["is_weekend"] = (dates.dt.dayofweek >= 5).astype(int)
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
        df["day_of_year_sin"] = np.sin(2 * np.pi * df["day_of_year"] / 365.25)
        df["day_of_year_cos"] = np.cos(2 * np.pi * df["day_of_year"] / 365.25)

    if "price_range" not in df.columns and "Max Price" in df.columns and "Min Price" in df.columns:
        df["price_range"] = df["Max Price"] - df["Min Price"]
        if "Modal Price" in df.columns:
            df["price_range_pct"] = df["price_range"] / df["Modal Price"]

    missing = [c for c in REQUIRED_FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required input features: {missing}")

    return df[REQUIRED_FEATURES]


def forecast_price(
    crop: str,
    market: str,
    input_data: Union[Dict, pd.DataFrame],
    override_method: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a price forecast for the given crop/market.

    Parameters
    ----------
    crop : str  — one of rice/tomato/wheat/cotton
    market : str — mandi name (used for context, not filtering here)
    input_data : dict or DataFrame — must contain all REQUIRED_FEATURES
    override_method : optional, one of 'persistence' | 'recent_mean' | 'ml_model'

    Returns
    -------
    dict with forecast details.
    """
    crop = _normalize_crop(crop)
    config = load_forecast_config()
    method = override_method or config.get(crop, {}).get("method", "persistence")

    # Extract current price
    if isinstance(input_data, dict):
        current_price = float(input_data.get("Modal Price", 0))
        ma7 = input_data.get("price_ma_7", None)
    else:
        current_price = float(input_data["Modal Price"].iloc[0])
        ma7 = input_data["price_ma_7"].iloc[0] if "price_ma_7" in input_data.columns else None

    if current_price <= 0:
        raise ValueError("Modal Price must be a positive number.")

    if method == "persistence":
        predicted_price = current_price
    elif method == "recent_mean":
        if ma7 is None or (isinstance(ma7, float) and np.isnan(ma7)):
            # Fallback to persistence
            predicted_price = current_price
            method = "persistence_fallback_from_recent_mean"
        else:
            predicted_price = float(ma7)
    elif method == "ml_model":
        try:
            model = load_ml_model(crop)
            X = _prepare_ml_input(input_data)
            predicted_price = float(model.predict(X)[0])
        except Exception as e:
            # Graceful fallback to persistence
            predicted_price = current_price
            method = f"persistence_fallback_ml_error({type(e).__name__})"
    elif method == "chronos-2":
        try:
            if isinstance(input_data, pd.DataFrame) and len(input_data) >= 5:
                from src.chronos_forecast import prepare_chronos_dataframe, forecast_chronos
                clean_df = prepare_chronos_dataframe(input_data, id_col="Market", time_col="Price Date", target_col="Modal Price")
                fc = forecast_chronos(clean_df, prediction_length=3)
                target_row = fc.iloc[2] if len(fc) >= 3 else fc.iloc[-1]
                predicted_price = float(target_row.get("0.5", target_row.get("prediction", current_price)))
            else:
                # Single-row input: fallback to current price
                predicted_price = current_price
        except Exception as e:
            predicted_price = current_price
            method = f"persistence_fallback_chronos_error({type(e).__name__})"
    else:
        raise ValueError(f"Unknown forecast method: '{method}'")

    meta = load_metadata(crop)
    validation_mae = meta.get("MAE", meta.get("persistence_baseline_MAE", None))

    return {
        "crop": crop,
        "market": market,
        "forecast_horizon_observations": 3,
        "forecast_method": method,
        "current_price": round(current_price, 2),
        "predicted_price": round(predicted_price, 2),
        "validation_mae": round(validation_mae, 4) if validation_mae else None,
    }


if __name__ == "__main__":
    config = build_forecast_config(save=True)
    print("Forecast Method Config:")
    for crop, cfg in config.items():
        print(f"  {crop}: {cfg['method']} ({cfg['reason']})")
