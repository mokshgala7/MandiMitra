"""
direction_features.py — Feature Engineering for MandiMitra ML V3 Direction Forecasting

Constructs:
1. Historical price features (lags, moving averages, momentum, volatility, calendar).
2. Cross-mandi spatial features (crop-wide mean, spread, relative rank, % markets increasing).
3. Chronos-2 features (foundation model forecasts and interval width).
4. Direction target labels (INCREASE, STABLE, DECREASE) using empirical crop thresholds.

Strict causality: zero future leakage. Cross-sectional aggregations only use observations
available at or before prediction date T.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

# Empirically selected movement thresholds based on training distribution
EMPIRICAL_THRESHOLDS = {
    "rice": 0.015,     # ±1.5% (distinguishes breakouts from ~68% sticky price regimes)
    "tomato": 0.050,   # ±5.0% (captures genuine surges/drops in high-volatility perishables)
    "wheat": 0.015,    # ±1.5% (cleanly separates stationary trading from meaningful trends)
    "cotton": 0.010,   # ±1.0% (captures meaningful moves in narrow seasonal price band)
}

LABEL_NAMES = {-1: "DECREASE", 0: "STABLE", 1: "INCREASE"}


def compute_direction_label(
    current_price: float,
    future_price: float,
    threshold_pct: float
) -> int:
    """
    Assign direction label based on percentage change:
    1: INCREASE (pct_change > threshold_pct)
    0: STABLE   (-threshold_pct <= pct_change <= threshold_pct)
   -1: DECREASE (pct_change < -threshold_pct)
    """
    if pd.isna(current_price) or pd.isna(future_price) or current_price <= 0:
        return np.nan
    pct_change = (future_price - current_price) / current_price
    if pct_change > threshold_pct:
        return 1
    elif pct_change < -threshold_pct:
        return -1
    else:
        return 0


def build_cross_mandi_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute cross-mandi features across active mandis on each reporting date.
    Strictly causal: groups by Price Date and computes cross-sectional aggregates.
    """
    df = df.copy()
    df["Price Date"] = pd.to_datetime(df["Price Date"])

    # Date-level cross-sectional aggregates
    date_grp = df.groupby("Price Date")["Modal Price"]
    date_stats = date_grp.agg(
        crop_mean_price="mean",
        crop_median_price="median",
        crop_min_price="min",
        crop_max_price="max",
        crop_std_price="std",
        crop_active_markets="count"
    ).reset_index()

    date_stats["crop_std_price"] = date_stats["crop_std_price"].fillna(0.0)
    date_stats["crop_price_spread"] = date_stats["crop_max_price"] - date_stats["crop_min_price"]

    # Trailing crop-wide momentum
    date_stats = date_stats.sort_values("Price Date").reset_index(drop=True)
    date_stats["crop_mean_lag_1"] = date_stats["crop_mean_price"].shift(1)
    date_stats["crop_mean_lag_3"] = date_stats["crop_mean_price"].shift(3)
    date_stats["crop_mean_change_1_pct"] = (date_stats["crop_mean_price"] - date_stats["crop_mean_lag_1"]) / date_stats["crop_mean_lag_1"]
    date_stats["crop_mean_change_3_pct"] = (date_stats["crop_mean_price"] - date_stats["crop_mean_lag_3"]) / date_stats["crop_mean_lag_3"]
    date_stats["crop_mean_change_1_pct"] = date_stats["crop_mean_change_1_pct"].fillna(0.0)
    date_stats["crop_mean_change_3_pct"] = date_stats["crop_mean_change_3_pct"].fillna(0.0)

    # Merge back
    df = df.merge(date_stats, on="Price Date", how="left")

    # Relative market features
    df["market_price_minus_crop_mean"] = df["Modal Price"] - df["crop_mean_price"]
    df["market_price_ratio_crop_mean"] = df["Modal Price"] / (df["crop_mean_price"] + 1e-6)

    # Market percentile rank by price on each date
    df["market_price_rank"] = df.groupby("Price Date")["Modal Price"].rank(pct=True)

    # % of active markets with positive trailing momentum
    if "price_change_3" in df.columns:
        pos_mom = df.groupby("Price Date")["price_change_3"].apply(lambda s: (s > 0).mean()).reset_index(name="crop_pct_markets_increasing")
        neg_mom = df.groupby("Price Date")["price_change_3"].apply(lambda s: (s < 0).mean()).reset_index(name="crop_pct_markets_decreasing")
        df = df.merge(pos_mom, on="Price Date", how="left")
        df = df.merge(neg_mom, on="Price Date", how="left")
    else:
        df["crop_pct_markets_increasing"] = 0.5
        df["crop_pct_markets_decreasing"] = 0.5

    return df


def attach_chronos_features(
    df: pd.DataFrame,
    chronos_forecasts_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Attach Chronos-2 foundation model predictions if available.
    """
    df = df.copy()
    if chronos_forecasts_path is None:
        chronos_forecasts_path = BASE_DIR / "outputs" / "final" / "chronos2_forecasts.csv"

    if chronos_forecasts_path.exists():
        cf = pd.read_csv(chronos_forecasts_path)
        cf["cutoff_date"] = pd.to_datetime(cf["cutoff_date"])
        df["Price Date"] = pd.to_datetime(df["Price Date"])

        # Join on market, cutoff_date, crop
        merged = df.merge(
            cf[["crop", "market", "cutoff_date", "chronos_pred", "chronos_p10", "chronos_p90"]],
            left_on=["Commodity", "Market", "Price Date"],
            right_on=["crop", "market", "cutoff_date"],
            how="left"
        )
        # Handle crop lowercase if needed
        if merged["chronos_pred"].isna().all():
            merged = df.merge(
                cf[["market", "cutoff_date", "chronos_pred", "chronos_p10", "chronos_p90"]],
                left_on=["Market", "Price Date"],
                right_on=["market", "cutoff_date"],
                how="left"
            )

        df["chronos_pred"] = merged["chronos_pred"].fillna(df["Modal Price"])
        df["chronos_p10"] = merged["chronos_p10"].fillna(df["Modal Price"] * 0.95)
        df["chronos_p90"] = merged["chronos_p90"].fillna(df["Modal Price"] * 1.05)
    else:
        # Fallback to persistence-based anchor if chronos outputs absent
        df["chronos_pred"] = df["Modal Price"]
        df["chronos_p10"] = df["Modal Price"] * 0.95
        df["chronos_p90"] = df["Modal Price"] * 1.05

    df["chronos_pred_diff"] = df["chronos_pred"] - df["Modal Price"]
    df["chronos_pred_pct"] = (df["chronos_pred"] - df["Modal Price"]) / (df["Modal Price"] + 1e-6)
    df["chronos_interval_width"] = df["chronos_p90"] - df["chronos_p10"]
    return df


def prepare_direction_dataset(
    crop: str,
    include_chronos: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, List[str]]]:
    """
    Loads train and test datasets for a crop, generates cross-mandi features,
    attaches Chronos-2 features, and creates the direction target labels.

    Returns
    -------
    train_df : pd.DataFrame
    test_df : pd.DataFrame
    feature_groups : dict with keys ['historical', 'cross_mandi', 'chronos', 'all']
    """
    train_path = BASE_DIR / "data" / "processed" / f"maharashtra_{crop}_train.csv"
    test_path = BASE_DIR / "data" / "processed" / f"maharashtra_{crop}_test.csv"

    train_df = pd.read_csv(train_path, low_memory=False)
    test_df = pd.read_csv(test_path, low_memory=False)

    threshold = EMPIRICAL_THRESHOLDS.get(crop.lower(), 0.015)

    # Compute target labels
    train_df["direction_label"] = [
        compute_direction_label(curr, fut, threshold)
        for curr, fut in zip(train_df["Modal Price"], train_df["price_after_3_observations"])
    ]
    test_df["direction_label"] = [
        compute_direction_label(curr, fut, threshold)
        for curr, fut in zip(test_df["Modal Price"], test_df["price_after_3_observations"])
    ]

    # Filter out missing targets
    train_df = train_df.dropna(subset=["direction_label"]).reset_index(drop=True)
    test_df = test_df.dropna(subset=["direction_label"]).reset_index(drop=True)
    train_df["direction_label"] = train_df["direction_label"].astype(int)
    test_df["direction_label"] = test_df["direction_label"].astype(int)

    # Generate cross-mandi features separately on train and test
    # (Train cross-mandi uses train dates; test cross-mandi uses test dates)
    train_df = build_cross_mandi_features(train_df)
    test_df = build_cross_mandi_features(test_df)

    if include_chronos:
        train_df = attach_chronos_features(train_df)
        test_df = attach_chronos_features(test_df)

    # Define feature groups
    hist_candidates = [
        "Modal Price", "Min Price", "Max Price",
        "price_lag_1", "price_lag_2", "price_lag_3", "price_lag_7", "price_lag_14", "price_lag_30",
        "price_ma_3", "price_ma_7", "price_ma_14", "price_ma_30",
        "price_std_7", "price_std_14", "price_std_30",
        "price_change_1", "price_change_1_pct", "price_change_3", "price_change_3_pct",
        "price_change_7", "price_change_7_pct", "price_change_14", "price_change_14_pct",
        "price_range", "price_range_pct",
        "year", "month", "day", "day_of_week", "day_of_year", "week_of_year", "is_weekend",
        "month_sin", "month_cos", "day_of_year_sin", "day_of_year_cos"
    ]
    hist_features = [c for c in hist_candidates if c in train_df.columns and c in test_df.columns]

    cross_candidates = [
        "crop_mean_price", "crop_median_price", "crop_min_price", "crop_max_price",
        "crop_std_price", "crop_active_markets", "crop_price_spread",
        "crop_mean_change_1_pct", "crop_mean_change_3_pct",
        "market_price_minus_crop_mean", "market_price_ratio_crop_mean",
        "market_price_rank", "crop_pct_markets_increasing", "crop_pct_markets_decreasing"
    ]
    cross_features = [c for c in cross_candidates if c in train_df.columns and c in test_df.columns]

    chronos_candidates = [
        "chronos_pred", "chronos_p10", "chronos_p90",
        "chronos_pred_diff", "chronos_pred_pct", "chronos_interval_width"
    ]
    chronos_features = [c for c in chronos_candidates if c in train_df.columns and c in test_df.columns]

    # Fill NaNs with column medians from training set
    for col in hist_features + cross_features + chronos_features:
        median_val = train_df[col].median()
        if pd.isna(median_val):
            median_val = 0.0
        train_df[col] = train_df[col].fillna(median_val)
        test_df[col] = test_df[col].fillna(median_val)

    feature_groups = {
        "historical": hist_features,
        "cross_mandi": hist_features + cross_features,
        "chronos": hist_features + chronos_features,
        "all": hist_features + cross_features + chronos_features
    }

    return train_df, test_df, feature_groups
