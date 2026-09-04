"""
Inference Interface for MandiMitra Price Forecasting.
Loads the trained model pipeline and provides clean prediction functions
for downstream services and decision support logic.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Union
import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = BASE_DIR / "models" / "mandimitra_rice_price_model.joblib"
DEFAULT_METADATA_PATH = BASE_DIR / "models" / "model_metadata.json"

_CACHED_MODEL = None
_CACHED_METADATA = None

EXPECTED_FEATURES = [
    "Min Price", "Max Price", "Modal Price",
    "price_lag_1", "price_lag_2", "price_lag_3", "price_lag_7", "price_lag_14", "price_lag_30",
    "price_ma_3", "price_ma_7", "price_ma_14", "price_ma_30",
    "price_std_7", "price_std_14", "price_std_30",
    "price_change_1", "price_change_1_pct", "price_change_3", "price_change_3_pct",
    "price_change_7", "price_change_7_pct", "price_change_14", "price_change_14_pct",
    "price_range", "price_range_pct",
    "year", "month", "day", "day_of_week", "day_of_year", "week_of_year", "is_weekend",
    "month_sin", "month_cos", "day_of_year_sin", "day_of_year_cos",
    "Market", "Variety", "Grade"
]


def load_model(model_path: Path = DEFAULT_MODEL_PATH):
    """Load and cache the trained model pipeline from joblib artifact."""
    global _CACHED_MODEL
    if _CACHED_MODEL is None:
        if not model_path.exists():
            raise FileNotFoundError(f"Trained model not found at {model_path}. Run training pipeline first.")
        _CACHED_MODEL = joblib.load(model_path)
    return _CACHED_MODEL


def load_metadata(metadata_path: Path = DEFAULT_METADATA_PATH) -> Dict[str, Any]:
    """Load model training and evaluation metadata."""
    global _CACHED_METADATA
    if _CACHED_METADATA is None:
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                _CACHED_METADATA = json.load(f)
        else:
            _CACHED_METADATA = {}
    return _CACHED_METADATA


def _prepare_input_df(data: Union[Dict[str, Any], pd.DataFrame]) -> pd.DataFrame:
    """Validate and format input data into an aligned DataFrame for the model pipeline."""
    if isinstance(data, dict):
        df = pd.DataFrame([data])
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise ValueError("Input data must be a dictionary or a pandas DataFrame.")

    # Auto-compute calendar features if Price Date is present and calendar fields are missing
    if "Price Date" in df.columns and "month_sin" not in df.columns:
        dates = pd.to_datetime(df["Price Date"])
        df["year"] = dates.dt.year
        df["month"] = dates.dt.month
        df["day"] = dates.dt.day
        df["day_of_week"] = dates.dt.dayofweek
        df["day_of_year"] = dates.dt.dayofyear
        df["week_of_year"] = dates.dt.isocalendar().week.astype(int)
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
        df["month_sin"] = np.sin(2.0 * np.pi * df["month"] / 12.0)
        df["month_cos"] = np.cos(2.0 * np.pi * df["month"] / 12.0)
        df["day_of_year_sin"] = np.sin(2.0 * np.pi * df["day_of_year"] / 365.25)
        df["day_of_year_cos"] = np.cos(2.0 * np.pi * df["day_of_year"] / 365.25)

    # Auto-compute price_range if missing
    if "price_range" not in df.columns and "Max Price" in df.columns and "Min Price" in df.columns:
        df["price_range"] = df["Max Price"] - df["Min Price"]
        if "Modal Price" in df.columns:
            df["price_range_pct"] = df["price_range"] / df["Modal Price"]

    # Verify all expected columns are present
    missing_cols = [c for c in EXPECTED_FEATURES if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns for prediction: {missing_cols}")

    return df[EXPECTED_FEATURES]


def predict_mandi_price(
    data: Union[Dict[str, Any], pd.DataFrame],
    model_path: Path = DEFAULT_MODEL_PATH
) -> Union[float, np.ndarray]:
    """
    Predict future Modal Price approximately 3 observations ahead (~3-4 calendar days).

    Parameters:
        data: Single dictionary or DataFrame containing the required feature attributes:
              - Market, Variety, Grade
              - Min Price, Max Price, Modal Price
              - price_lag_1 .. price_lag_30
              - price_ma_3 .. price_ma_30, price_std_7 .. price_std_30
              - price_change_1 .. price_change_14 (abs & pct)
              - price_range, price_range_pct
              - Calendar & cyclical seasonal attributes (or Price Date)
        model_path: Optional custom path to trained .joblib model.

    Returns:
        predicted_price: Float for single dictionary input, or numpy array of predictions.
    """
    model = load_model(model_path)
    X = _prepare_input_df(data)
    predictions = model.predict(X)

    if isinstance(data, dict):
        return float(round(predictions[0], 2))
    return np.round(predictions, 2)


def main():
    """Smoke test inference with a sample test observation."""
    print("Testing MandiMitra inference pipeline...")
    test_csv = BASE_DIR / "data" / "processed" / "maharashtra_rice_test.csv"
    if not test_csv.exists():
        print(f"Test dataset not found at {test_csv}.")
        return

    df_test = pd.read_csv(test_csv).dropna(subset=EXPECTED_FEATURES + ["price_after_3_observations"])
    sample_row = df_test.iloc[0].to_dict()

    print(f"Sample Mandi: {sample_row['Market']} | Variety: {sample_row['Variety']} | Grade: {sample_row['Grade']}")
    print(f"Sample Date: {sample_row['Price Date']} | Current Modal Price: ₹{sample_row['Modal Price']}")
    print(f"Actual Target (3 obs ahead): ₹{sample_row['price_after_3_observations']}")

    predicted = predict_mandi_price(sample_row)
    print(f"Model Forecast (3 obs ahead): ₹{predicted:.2f}")
    print("Inference interface operational.")


if __name__ == "__main__":
    main()
