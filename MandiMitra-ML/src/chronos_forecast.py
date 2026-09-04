"""
chronos_forecast.py — MandiMitra Amazon Chronos-2 Forecasting Pipeline

Provides zero-shot and in-context probabilistic forecasting for mandi market series
using Amazon's Chronos-2 universal time series foundation model.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import torch

BASE_DIR = Path(__file__).resolve().parent.parent
CHRONOS_MODEL_ID = "amazon/chronos-2"

_PIPELINE_CACHE: Dict[str, Any] = {}


def get_chronos_pipeline(device: Optional[str] = None):
    """
    Load and cache Chronos2Pipeline.
    Defaults to 'mps' if available on Apple Silicon, else 'cpu'.
    """
    global _PIPELINE_CACHE
    if device is None:
        if torch.backends.mps.is_available():
            device = "cpu"  # Keep CPU for stability unless specified
        else:
            device = "cpu"

    if device not in _PIPELINE_CACHE:
        from chronos import Chronos2Pipeline
        print(f"Loading {CHRONOS_MODEL_ID} on device={device}...")
        _PIPELINE_CACHE[device] = Chronos2Pipeline.from_pretrained(
            CHRONOS_MODEL_ID,
            device_map=device
        )
    return _PIPELINE_CACHE[device]


def prepare_chronos_dataframe(
    df: pd.DataFrame,
    id_col: str = "Market",
    time_col: str = "Price Date",
    target_col: str = "Modal Price"
) -> pd.DataFrame:
    """
    Format historical mandi records into Chronos-2 expected schema:
    [id, timestamp, target].
    
    Mandi markets have irregular reporting dates (trading days skip weekends/holidays).
    To prevent invalid calendar forward-filling or Chronos frequency-inference failures,
    we represent sequential market observations using an observation-index frequency.
    Each step in Chronos-2 then corresponds directly to observation t+1, t+2, t+3.
    """
    clean_df = df[[id_col, time_col, target_col]].copy()
    clean_df[time_col] = pd.to_datetime(clean_df[time_col])
    clean_df = clean_df.sort_values(by=[id_col, time_col]).reset_index(drop=True)
    clean_df["timestamp"] = clean_df.groupby(id_col).cumcount().apply(
        lambda c: pd.Timestamp("2020-01-01") + pd.Timedelta(days=c)
    )
    clean_df = clean_df.rename(columns={
        id_col: "id",
        target_col: "target"
    })
    return clean_df[["id", "timestamp", "target"]]


def forecast_chronos(
    context_df: pd.DataFrame,
    prediction_length: int = 3,
    quantile_levels: List[float] = [0.1, 0.5, 0.9],
    cross_mandi_joint: bool = False,
    device: Optional[str] = None
) -> pd.DataFrame:
    """
    Generate multi-step quantile forecasts using Chronos-2.

    Parameters
    ----------
    context_df : pd.DataFrame
        DataFrame with columns ['id', 'timestamp', 'target'].
    prediction_length : int
        Number of steps forward to forecast (e.g. 3 observations).
    quantile_levels : list of float
        Quantiles for probabilistic intervals (e.g. [0.1, 0.5, 0.9]).
    cross_mandi_joint : bool
        If True, enables joint batch forecasting across related mandis
        (cross-series in-context learning).
    device : str, optional
        Computation device ('cpu', 'cuda').

    Returns
    -------
    forecast_df : pd.DataFrame
        Predictions with quantiles, series id, and forecast horizon steps.
    """
    pipeline = get_chronos_pipeline(device=device)

    # predict_df call with cross_learning
    kwargs = {
        "prediction_length": prediction_length,
        "quantile_levels": quantile_levels,
        "id_column": "id",
        "timestamp_column": "timestamp",
        "target": "target"
    }
    if cross_mandi_joint:
        try:
            forecast = pipeline.predict_df(context_df, cross_learning=True, **kwargs)
        except TypeError:
            forecast = pipeline.predict_df(context_df, predict_batches_jointly=True, **kwargs)
    else:
        forecast = pipeline.predict_df(context_df, **kwargs)

    return forecast
