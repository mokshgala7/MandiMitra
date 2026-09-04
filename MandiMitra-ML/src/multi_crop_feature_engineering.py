"""
Multi-Crop Feature Engineering for MandiMitra ML Pipeline.
Engineered features are calculated independently within each Market+Variety+Grade series.
No data leakage; no imputation; no forward-fill.
Rice files are not touched.
"""

from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

MODELING_PATHS = {
    "Tomato": PROCESSED_DIR / "maharashtra_tomato_modeling_clean.csv",
    "Wheat": PROCESSED_DIR / "maharashtra_wheat_modeling_clean.csv",
    "Cotton": PROCESSED_DIR / "maharashtra_cotton_modeling_clean.csv",
}
FEATURES_OUTPUT_PATHS = {
    "Tomato": PROCESSED_DIR / "maharashtra_tomato_features.csv",
    "Wheat": PROCESSED_DIR / "maharashtra_wheat_features.csv",
    "Cotton": PROCESSED_DIR / "maharashtra_cotton_features.csv",
}

DATE_COL = "Price Date"
GROUP_COLS = ["Market", "Variety", "Grade"]
PRICE_COL = "Modal Price"


def _strip_numeric(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
        .replace("nan", np.nan)
        .astype(float)
    )


def engineer_group_features(grp: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer all features for ONE Market+Variety+Grade group,
    sorted chronologically. All lag/rolling operations are observation-based
    (not calendar-based) to respect irregular reporting without interpolation.
    """
    grp = grp.sort_values(DATE_COL).reset_index(drop=True)
    price = grp[PRICE_COL].copy()

    # --- Lag features (observation-based, not calendar-based) ---
    grp["price_lag_1"] = price.shift(1)
    grp["price_lag_2"] = price.shift(2)
    grp["price_lag_3"] = price.shift(3)
    grp["price_lag_7"] = price.shift(7)
    grp["price_lag_14"] = price.shift(14)
    grp["price_lag_30"] = price.shift(30)

    # --- Rolling means (window = # observations) ---
    grp["price_ma_3"] = price.shift(1).rolling(window=3, min_periods=3).mean()
    grp["price_ma_7"] = price.shift(1).rolling(window=7, min_periods=7).mean()
    grp["price_ma_14"] = price.shift(1).rolling(window=14, min_periods=14).mean()
    grp["price_ma_30"] = price.shift(1).rolling(window=30, min_periods=30).mean()

    # --- Rolling standard deviations ---
    grp["price_std_7"] = price.shift(1).rolling(window=7, min_periods=7).std()
    grp["price_std_14"] = price.shift(1).rolling(window=14, min_periods=14).std()
    grp["price_std_30"] = price.shift(1).rolling(window=30, min_periods=30).std()

    # --- Momentum features ---
    grp["price_change_1"] = price - price.shift(1)
    grp["price_change_1_pct"] = grp["price_change_1"] / price.shift(1)
    grp["price_change_3"] = price - price.shift(3)
    grp["price_change_3_pct"] = grp["price_change_3"] / price.shift(3)
    grp["price_change_7"] = price - price.shift(7)
    grp["price_change_7_pct"] = grp["price_change_7"] / price.shift(7)
    grp["price_change_14"] = price - price.shift(14)
    grp["price_change_14_pct"] = grp["price_change_14"] / price.shift(14)

    # --- Price spread features ---
    grp["price_range"] = grp["Max Price"] - grp["Min Price"]
    grp["price_range_pct"] = grp["price_range"] / grp["Modal Price"]

    # --- Calendar / seasonal features ---
    dates = grp[DATE_COL]
    grp["year"] = dates.dt.year
    grp["month"] = dates.dt.month
    grp["day"] = dates.dt.day
    grp["day_of_week"] = dates.dt.dayofweek
    grp["day_of_year"] = dates.dt.dayofyear
    grp["week_of_year"] = dates.dt.isocalendar().week.astype(int)
    grp["is_weekend"] = (dates.dt.dayofweek >= 5).astype(int)

    # Cyclical encoding
    grp["month_sin"] = np.sin(2.0 * np.pi * grp["month"] / 12.0)
    grp["month_cos"] = np.cos(2.0 * np.pi * grp["month"] / 12.0)
    grp["day_of_year_sin"] = np.sin(2.0 * np.pi * grp["day_of_year"] / 365.25)
    grp["day_of_year_cos"] = np.cos(2.0 * np.pi * grp["day_of_year"] / 365.25)

    # --- Candidate target variables (strictly forward-looking, no leakage) ---
    grp["price_next_observation"] = price.shift(-1)
    grp["price_after_3_observations"] = price.shift(-3)
    grp["price_after_7_observations"] = price.shift(-7)
    grp["future_price_change_3"] = grp["price_after_3_observations"] - price
    grp["future_price_change_7"] = grp["price_after_7_observations"] - price

    # Track target realization dates for purging during split
    grp["target_date_3"] = grp[DATE_COL].shift(-3)
    grp["target_date_7"] = grp[DATE_COL].shift(-7)

    return grp


def engineer_features_for_crop(crop: str, verbose: bool = True) -> pd.DataFrame:
    """
    Load clean modeling data, engineer features group-by-group,
    concatenate and save.
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"FEATURE ENGINEERING: {crop.upper()}")
        print(f"{'='*60}")

    path = MODELING_PATHS[crop]
    if not path.exists():
        raise FileNotFoundError(f"Modeling clean CSV not found: {path}. Run multi_crop_cleaning.py first.")

    df = pd.read_csv(path, low_memory=False)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
    for col in ["Min Price", "Max Price", "Modal Price"]:
        df[col] = _strip_numeric(df[col])

    if df.empty:
        if verbose:
            print(f"  WARNING: No retained data for {crop}. Skipping feature engineering.")
        return pd.DataFrame()

    group_frames = []
    for keys, grp in df.groupby(GROUP_COLS, sort=True):
        mkt, var, grade = keys
        engineered = engineer_group_features(grp)
        group_frames.append(engineered)
        if verbose:
            print(f"  {mkt} | {var} | {grade}: {len(grp)} obs -> {engineered['price_after_3_observations'].notna().sum()} valid 3-obs targets")

    features_df = pd.concat(group_frames, ignore_index=True)
    features_df = features_df.sort_values([DATE_COL, "Market", "Variety", "Grade"]).reset_index(drop=True)

    # Leakage check: no target columns in feature space
    target_columns = ["price_next_observation", "price_after_3_observations", "price_after_7_observations",
                      "future_price_change_3", "future_price_change_7", "target_date_3", "target_date_7"]
    feature_cols = [c for c in features_df.columns if c not in target_columns]

    FEATURES_OUTPUT_PATHS[crop].parent.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(FEATURES_OUTPUT_PATHS[crop], index=False)

    if verbose:
        n_feature_cols = len([c for c in feature_cols if c not in [DATE_COL, "Market", "Variety", "Grade",
                                                                     "State/UT", "District", "Commodity Group",
                                                                     "Commodity", "Price Unit",
                                                                     "price_order_flag", "statistical_outlier_flag"]])
        print(f"  Total rows in features dataset: {len(features_df):,}")
        print(f"  Saved: {FEATURES_OUTPUT_PATHS[crop].relative_to(BASE_DIR)}")

    return features_df


def engineer_all_crops(verbose: bool = True) -> dict:
    """Engineer features for all three crops and return dict of DataFrames."""
    results = {}
    for crop in ["Tomato", "Wheat", "Cotton"]:
        feat_df = engineer_features_for_crop(crop, verbose=verbose)
        results[crop] = feat_df
    return results


if __name__ == "__main__":
    engineer_all_crops(verbose=True)
