"""
Multi-Crop Inference Interface for MandiMitra ML Pipeline.
Loads trained model pipelines for Tomato, Wheat, and Cotton and provides
a clean predict_price() function for downstream use by the backend team.

Rice inference is handled by src/predict.py — this script does NOT touch it.
"""

import json
from pathlib import Path
from typing import Any, Dict, Union

import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

MODEL_PATHS = {
    "tomato": MODELS_DIR / "mandimitra_tomato_price_model.joblib",
    "wheat": MODELS_DIR / "mandimitra_wheat_price_model.joblib",
    "cotton": MODELS_DIR / "mandimitra_cotton_price_model.joblib",
}
METADATA_PATHS = {
    "tomato": MODELS_DIR / "tomato_model_metadata.json",
    "wheat": MODELS_DIR / "wheat_model_metadata.json",
    "cotton": MODELS_DIR / "cotton_model_metadata.json",
}

SUPPORTED_CROPS = list(MODEL_PATHS.keys())

# Cache loaded models in memory
_MODEL_CACHE: Dict[str, Any] = {}
_METADATA_CACHE: Dict[str, Any] = {}

EXPECTED_FEATURES = [
    "Min Price", "Max Price", "Modal Price",
    "price_lag_1", "price_lag_2", "price_lag_3",
    "price_lag_7", "price_lag_14", "price_lag_30",
    "price_ma_3", "price_ma_7", "price_ma_14", "price_ma_30",
    "price_std_7", "price_std_14", "price_std_30",
    "price_change_1", "price_change_1_pct",
    "price_change_3", "price_change_3_pct",
    "price_change_7", "price_change_7_pct",
    "price_change_14", "price_change_14_pct",
    "price_range", "price_range_pct",
    "year", "month", "day", "day_of_week", "day_of_year",
    "week_of_year", "is_weekend",
    "month_sin", "month_cos", "day_of_year_sin", "day_of_year_cos",
    "Market", "Variety", "Grade",
]


def _normalize_crop(crop: str) -> str:
    normalized = crop.strip().lower()
    if normalized not in SUPPORTED_CROPS:
        raise ValueError(
            f"Unsupported crop: '{crop}'. Supported crops: {SUPPORTED_CROPS}. "
            "For Rice, use src/predict.py."
        )
    return normalized


def load_model(crop: str) -> Any:
    """Load and cache the trained pipeline for a given crop."""
    crop = _normalize_crop(crop)
    if crop not in _MODEL_CACHE:
        model_path = MODEL_PATHS[crop]
        if not model_path.exists():
            raise FileNotFoundError(
                f"No trained model found for {crop} at {model_path}. "
                "Run src/multi_crop_train.py first."
            )
        _MODEL_CACHE[crop] = joblib.load(model_path)
    return _MODEL_CACHE[crop]


def load_metadata(crop: str) -> Dict[str, Any]:
    """Load and cache model metadata for a given crop."""
    crop = _normalize_crop(crop)
    if crop not in _METADATA_CACHE:
        meta_path = METADATA_PATHS[crop]
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                _METADATA_CACHE[crop] = json.load(f)
        else:
            _METADATA_CACHE[crop] = {}
    return _METADATA_CACHE[crop]


def _prepare_input_df(
    crop: str,
    data: Union[Dict[str, Any], pd.DataFrame],
) -> pd.DataFrame:
    """
    Validate and prepare input data as a DataFrame aligned to EXPECTED_FEATURES.
    Auto-computes calendar features if 'Price Date' is present but calendar fields are missing.
    """
    if isinstance(data, dict):
        df = pd.DataFrame([data])
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise TypeError("Input data must be a dict or pd.DataFrame.")

    # Auto-derive calendar features if only Price Date is provided
    if "Price Date" in df.columns and "month_sin" not in df.columns:
        dates = pd.to_datetime(df["Price Date"])
        df["year"] = dates.dt.year
        df["month"] = dates.dt.month
        df["day"] = dates.dt.day
        df["day_of_week"] = dates.dt.dayofweek
        df["day_of_year"] = dates.dt.dayofyear
        df["week_of_year"] = dates.dt.isocalendar().week.astype(int)
        df["is_weekend"] = (dates.dt.dayofweek >= 5).astype(int)
        df["month_sin"] = np.sin(2.0 * np.pi * df["month"] / 12.0)
        df["month_cos"] = np.cos(2.0 * np.pi * df["month"] / 12.0)
        df["day_of_year_sin"] = np.sin(2.0 * np.pi * df["day_of_year"] / 365.25)
        df["day_of_year_cos"] = np.cos(2.0 * np.pi * df["day_of_year"] / 365.25)

    # Auto-derive price_range if missing
    if "price_range" not in df.columns and "Max Price" in df.columns and "Min Price" in df.columns:
        df["price_range"] = df["Max Price"] - df["Min Price"]
        if "Modal Price" in df.columns:
            df["price_range_pct"] = df["price_range"] / df["Modal Price"]

    # Validate required features are present
    available = set(df.columns)
    missing = [f for f in EXPECTED_FEATURES if f not in available]
    if missing:
        raise ValueError(
            f"Missing required features for {crop} prediction: {missing}"
        )

    return df[EXPECTED_FEATURES]


def predict_price(
    crop: str,
    data: Union[Dict[str, Any], pd.DataFrame],
) -> Dict[str, Any]:
    """
    Predict future Modal Price approximately 3 observations ahead for the given crop.

    Parameters
    ----------
    crop : str
        One of 'tomato', 'wheat', 'cotton' (case-insensitive).
        For 'rice', use src/predict.py instead.
    data : dict or pd.DataFrame
        Input features. Must contain all EXPECTED_FEATURES, or at minimum:
        Market, Variety, Grade, Min Price, Max Price, Modal Price,
        price_lag_1 .. price_lag_30, price_ma_3 .. price_ma_30,
        price_std_7 .. price_std_30, price_change_* columns,
        price_range, price_range_pct, and calendar/cyclical features
        (or Price Date for auto-derivation).

    Returns
    -------
    dict with keys:
        crop           : normalized crop name
        market         : Market value from input
        variety        : Variety value from input
        grade          : Grade value from input
        predicted_price: float, predicted Modal Price ~3 obs ahead (₹/quintal)
    """
    normalized = _normalize_crop(crop)
    model = load_model(normalized)
    X = _prepare_input_df(normalized, data)

    predictions = model.predict(X)

    # Extract identifiers from first row for response context
    first = X.iloc[0]
    market = str(first.get("Market", "")) if hasattr(first, "get") else str(first["Market"])
    variety = str(first.get("Variety", "")) if hasattr(first, "get") else str(first["Variety"])
    grade = str(first.get("Grade", "")) if hasattr(first, "get") else str(first["Grade"])

    if isinstance(data, dict):
        return {
            "crop": normalized,
            "market": market,
            "variety": variety,
            "grade": grade,
            "predicted_price": float(round(predictions[0], 2)),
        }
    else:
        return {
            "crop": normalized,
            "market": market,
            "variety": variety,
            "grade": grade,
            "predicted_price": np.round(predictions, 2).tolist(),
        }


def main():
    """Smoke test inference for all three crops using one sample test row."""
    print("MandiMitra Multi-Crop Inference — Self-Test")
    print("=" * 50)

    test_file_map = {
        "tomato": BASE_DIR / "data" / "processed" / "maharashtra_tomato_test.csv",
        "wheat": BASE_DIR / "data" / "processed" / "maharashtra_wheat_test.csv",
        "cotton": BASE_DIR / "data" / "processed" / "maharashtra_cotton_test.csv",
    }

    for crop in SUPPORTED_CROPS:
        test_csv = test_file_map[crop]
        if not test_csv.exists():
            print(f"  {crop}: test file not found, skipping.")
            continue
        try:
            df_test = pd.read_csv(test_csv).dropna(subset=EXPECTED_FEATURES + ["price_after_3_observations"])
            if df_test.empty:
                print(f"  {crop}: no valid test rows, skipping.")
                continue
            sample = df_test.iloc[0].to_dict()
            result = predict_price(crop, sample)
            actual = float(sample["price_after_3_observations"])
            print(f"\n  {crop.upper()}")
            print(f"    Market  : {result['market']}")
            print(f"    Variety : {result['variety']}")
            print(f"    Grade   : {result['grade']}")
            print(f"    Current Modal Price      : ₹{float(sample['Modal Price']):.2f}")
            print(f"    Actual (3 obs ahead)     : ₹{actual:.2f}")
            print(f"    Predicted (3 obs ahead)  : ₹{result['predicted_price']:.2f}")
        except Exception as e:
            print(f"  {crop}: ERROR — {e}")

    print("\nInference interface operational.")


if __name__ == "__main__":
    main()
