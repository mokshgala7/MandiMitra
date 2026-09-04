"""
inference.py — MandiMitra Backend Inference Interface

Primary entry point for the Flask backend to obtain price forecasts.
Supports Amazon Chronos-2 foundation model forecasting (validated winner for Wheat)
and Persistence baseline forecasting (validated winner for Rice, Tomato, Cotton).

Strictly performs price prediction and does NOT make business decisions
(SELL/WAIT) or calculate transport/net revenues.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np

# Ensure src is in python path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.forecast_engine import (
    forecast_price, 
    load_forecast_config, 
    load_metadata, 
    _normalize_crop
)
from src.chronos_forecast import (
    prepare_chronos_dataframe,
    forecast_chronos
)

def _get_historical_series_for_mandi(crop: str, market: str) -> pd.DataFrame:
    """
    Retrieve historical price series for a given crop and market.
    """
    features_path = BASE_DIR / "data" / "processed" / f"maharashtra_{crop}_features.csv"
    if not features_path.exists():
        return pd.DataFrame()
        
    try:
        df = pd.read_csv(features_path, low_memory=False)
        df_market = df[df["Market"] == market].copy()
        if df_market.empty:
            return pd.DataFrame()
        df_market["Price Date"] = pd.to_datetime(df_market["Price Date"])
        df_market = df_market.sort_values(by="Price Date").reset_index(drop=True)
        return df_market[["Market", "Price Date", "Modal Price"]]
    except Exception:
        return pd.DataFrame()


def _get_latest_historical_features(crop: str, market: str) -> Dict[str, Any]:
    """
    Retrieve the most recent historical features for a given crop and market
    to support ML models (lags, moving averages, etc).
    """
    features_path = BASE_DIR / "data" / "processed" / f"maharashtra_{crop}_features.csv"
    if not features_path.exists():
        return {}
        
    try:
        df = pd.read_csv(features_path, low_memory=False)
        df_market = df[df["Market"] == market]
        if df_market.empty:
            return {}
            
        latest_row = df_market.sort_values(by="Price Date").iloc[-1]
        return latest_row.to_dict()
    except Exception:
        return {}


def estimate_simple_uncertainty(predicted_price: float, mae: float) -> Dict[str, Any]:
    """
    Empirical MAE-based prediction interval for baseline methods.
    """
    if mae is None or mae <= 0 or predicted_price <= 0:
        return {
            "level": "UNKNOWN",
            "lower_bound": None,
            "upper_bound": None
        }
        
    lower = max(0, predicted_price - mae)
    upper = predicted_price + mae
    
    unc_pct = (mae / predicted_price) * 100
    if unc_pct < 5.0:
        level = "LOW"
    elif unc_pct < 15.0:
        level = "MEDIUM"
    else:
        level = "HIGH"
        
    return {
        "level": level,
        "lower_bound": round(lower, 2),
        "upper_bound": round(upper, 2)
    }


def predict_price(crop: str, market: str, current_price: float, date: str) -> Dict[str, Any]:
    """
    Predict the future price for a given crop and market approximately 3 observations ahead.
    
    This function is the primary entry point for backend integration.
    
    Parameters
    ----------
    crop : str
        The crop name ('rice', 'tomato', 'wheat', 'cotton').
    market : str
        The APMC market name.
    current_price : float
        Today's Modal Price in ₹/quintal.
    date : str
        The current date (YYYY-MM-DD).
        
    Returns
    -------
    dict
        JSON-serializable dictionary containing the forecast.
    """
    # 1. Validation
    try:
        crop_norm = _normalize_crop(crop)
    except ValueError as e:
        return {"error": str(e)}
        
    if not isinstance(current_price, (int, float)) or current_price <= 0:
        return {"error": f"Invalid current_price: {current_price}"}
        
    # 2. Get configuration
    config = load_forecast_config()
    crop_config = config.get(crop_norm, {})
    method = crop_config.get("method", "persistence")
    
    # 3. Handle Chronos-2 Foundation Model Forecasting
    if method == "chronos-2":
        hist_df = _get_historical_series_for_mandi(crop_norm, market)
        if not hist_df.empty and len(hist_df) >= 5:
            try:
                # Append today's observation to context
                today_row = pd.DataFrame([{
                    "Market": market,
                    "Price Date": pd.to_datetime(date),
                    "Modal Price": float(current_price)
                }])
                context_full = pd.concat([hist_df, today_row], ignore_index=True)
                
                # Window up to last 90 observations
                context_window = context_full.iloc[-90:].copy()
                clean_context = prepare_chronos_dataframe(
                    context_window,
                    id_col="Market",
                    time_col="Price Date",
                    target_col="Modal Price"
                )
                
                # Predict 3 observations ahead
                fc_df = forecast_chronos(
                    clean_context,
                    prediction_length=3,
                    quantile_levels=[0.1, 0.5, 0.9],
                    cross_mandi_joint=False
                )
                
                if len(fc_df) >= 3:
                    target_row = fc_df.iloc[2] # 3rd observation ahead
                    p50 = float(target_row.get("0.5", target_row.get("prediction", current_price)))
                    p10 = float(target_row.get("0.1", p50 - 50.0))
                    p90 = float(target_row.get("0.9", p50 + 50.0))
                    
                    unc_level = "LOW" if ((p90 - p10) / p50) < 0.10 else "MEDIUM"
                    
                    return {
                        "crop": crop_norm,
                        "market": market,
                        "current_price": float(current_price),
                        "predicted_price": round(p50, 2),
                        "predicted_prices": [round(p50, 2)],
                        "forecast_method": "chronos-2",
                        "forecast_horizon": "3 market observations",
                        "uncertainty": {
                            "level": unc_level,
                            "lower_bound": round(p10, 2),
                            "upper_bound": round(p90, 2)
                        }
                    }
            except Exception as e:
                # Fallback gracefully to persistence if Chronos fails
                pass

    # 4. Standard Fallback / Persistence / ML Pipeline
    meta = load_metadata(crop_norm)
    mae = meta.get("MAE", meta.get("persistence_baseline_MAE", 0.0))
    hist_features = _get_latest_historical_features(crop_norm, market)
    
    if not hist_features:
        if method == "ml_model":
            method = "persistence"
        input_data = {"Modal Price": current_price, "Price Date": date, "Market": market}
    else:
        input_data = hist_features.copy()
        input_data["Modal Price"] = current_price
        input_data["Price Date"] = date
        
    try:
        forecast_result = forecast_price(
            crop=crop_norm,
            market=market,
            input_data=input_data,
            override_method="persistence" if method == "chronos-2" else method
        )
        predicted_val = forecast_result["predicted_price"]
        method_used = forecast_result["forecast_method"]
    except Exception:
        predicted_val = current_price
        method_used = "persistence"
        
    unc = estimate_simple_uncertainty(predicted_val, forecast_result.get("validation_mae", mae) if 'forecast_result' in locals() else mae)
    
    return {
        "crop": crop_norm,
        "market": market,
        "current_price": float(current_price),
        "predicted_price": round(float(predicted_val), 2),
        "predicted_prices": [round(float(predicted_val), 2)],
        "forecast_method": method_used,
        "forecast_horizon": "3 market observations",
        "uncertainty": unc
    }
