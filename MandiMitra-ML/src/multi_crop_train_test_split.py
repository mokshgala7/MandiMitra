"""
Multi-Crop Chronological Train/Test Split and Target Selection for MandiMitra ML Pipeline.
Performs strict 80/20 chronological split per crop, independently.
No random shuffling; no data leakage; no fabricated observations.
Rice files are not touched.
"""

from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUTS_DIR = BASE_DIR / "outputs"

FEATURES_PATHS = {
    "Tomato": PROCESSED_DIR / "maharashtra_tomato_features.csv",
    "Wheat": PROCESSED_DIR / "maharashtra_wheat_features.csv",
    "Cotton": PROCESSED_DIR / "maharashtra_cotton_features.csv",
}
TRAIN_OUTPUT_PATHS = {
    "Tomato": PROCESSED_DIR / "maharashtra_tomato_train.csv",
    "Wheat": PROCESSED_DIR / "maharashtra_wheat_train.csv",
    "Cotton": PROCESSED_DIR / "maharashtra_cotton_train.csv",
}
TEST_OUTPUT_PATHS = {
    "Tomato": PROCESSED_DIR / "maharashtra_tomato_test.csv",
    "Wheat": PROCESSED_DIR / "maharashtra_wheat_test.csv",
    "Cotton": PROCESSED_DIR / "maharashtra_cotton_test.csv",
}
TARGET_COMP_PATHS = {
    "Tomato": OUTPUTS_DIR / "target_selection" / "tomato_target_comparison.csv",
    "Wheat": OUTPUTS_DIR / "target_selection" / "wheat_target_comparison.csv",
    "Cotton": OUTPUTS_DIR / "target_selection" / "cotton_target_comparison.csv",
}
SPLIT_SUMMARY_PATHS = {
    "Tomato": OUTPUTS_DIR / "splits" / "tomato_split_summary.csv",
    "Wheat": OUTPUTS_DIR / "splits" / "wheat_split_summary.csv",
    "Cotton": OUTPUTS_DIR / "splits" / "cotton_split_summary.csv",
}

DATE_COL = "Price Date"
GROUP_COLS = ["Market", "Variety", "Grade"]
PRICE_COL = "Modal Price"
CANDIDATES = ["price_next_observation", "price_after_3_observations", "price_after_7_observations"]


def _strip_numeric(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
        .replace("nan", np.nan)
        .astype(float)
    )


def compute_persistence_mae(df: pd.DataFrame, target_col: str) -> float:
    """Persistence baseline: predict current Modal Price as forecast."""
    valid = df[[PRICE_COL, target_col]].dropna()
    if len(valid) == 0:
        return np.nan
    return float(np.abs(valid[PRICE_COL] - valid[target_col]).mean())


def compute_ma7_mae(df: pd.DataFrame, target_col: str) -> float:
    """MA-7 baseline: predict rolling 7-obs mean as forecast."""
    valid = df[["price_ma_7", target_col]].dropna()
    if len(valid) == 0:
        return np.nan
    return float(np.abs(valid["price_ma_7"] - valid[target_col]).mean())


def compare_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Compare candidate target columns and produce selection report."""
    rows = []
    for tgt in CANDIDATES:
        if tgt not in df.columns:
            continue
        valid = df[tgt].dropna()
        rows.append({
            "target": tgt,
            "valid_observations": len(valid),
            "mean": round(float(valid.mean()), 2) if len(valid) else np.nan,
            "median": round(float(valid.median()), 2) if len(valid) else np.nan,
            "std": round(float(valid.std()), 2) if len(valid) else np.nan,
            "min": round(float(valid.min()), 2) if len(valid) else np.nan,
            "max": round(float(valid.max()), 2) if len(valid) else np.nan,
            "persistence_MAE": round(compute_persistence_mae(df, tgt), 4),
            "ma7_MAE": round(compute_ma7_mae(df, tgt), 4),
        })
    return pd.DataFrame(rows)


def select_primary_target(df: pd.DataFrame, crop: str) -> str:
    """
    Select the primary forecast target based on data characteristics.
    Default: price_after_3_observations unless data strongly suggests otherwise.
    Cotton (sparse/seasonal) and very short series may benefit from price_next_observation.
    """
    comp = compare_targets(df)
    if comp.empty:
        return "price_after_3_observations"

    # Count valid observations per target
    three_obs = comp[comp.target == "price_after_3_observations"]["valid_observations"].values
    next_obs = comp[comp.target == "price_next_observation"]["valid_observations"].values

    three_count = int(three_obs[0]) if len(three_obs) else 0
    next_count = int(next_obs[0]) if len(next_obs) else 0

    # For Cotton (data-constrained), consider next_observation if 3-obs target is too sparse
    if crop == "Cotton" and three_count < 200:
        return "price_next_observation"

    # Default to 3-observation horizon (practically useful, ~3-4 days ahead)
    return "price_after_3_observations"


def chronological_split(df: pd.DataFrame, target_col: str, crop: str, verbose: bool = True) -> tuple:
    """
    Perform strict 80/20 chronological split.
    Purge boundary records where target realization date exceeds cutoff.
    Returns (train_df, test_df, summary_dict).
    """
    df = df.sort_values(DATE_COL).reset_index(drop=True)
    all_dates = df[DATE_COL].sort_values().reset_index(drop=True)
    cutoff_idx = int(len(all_dates) * 0.80) - 1
    cutoff_date = all_dates.iloc[cutoff_idx]

    if verbose:
        print(f"  80/20 Cutoff date: {cutoff_date.date()}")

    # Determine target realization date column (use 3-obs or 7-obs date tracking if available)
    if target_col == "price_after_3_observations" and "target_date_3" in df.columns:
        target_date_col = "target_date_3"
    elif target_col == "price_after_7_observations" and "target_date_7" in df.columns:
        target_date_col = "target_date_7"
    else:
        target_date_col = None

    train_df = df[df[DATE_COL] <= cutoff_date].copy()
    test_df = df[df[DATE_COL] > cutoff_date].copy()

    # Purge training boundary records where target hasn't yet materialized
    rows_before_purge = len(train_df)
    if target_date_col and target_date_col in train_df.columns:
        train_df[target_date_col] = pd.to_datetime(train_df[target_date_col], errors="coerce")
        purge_mask = train_df[target_date_col] > cutoff_date
        purge_mask |= train_df[target_col].isna()
        train_df = train_df[~purge_mask].copy()
    else:
        train_df = train_df.dropna(subset=[target_col])
    rows_purged = rows_before_purge - len(train_df)

    valid_test = test_df.dropna(subset=[target_col])

    summary = {
        "crop": crop,
        "primary_target": target_col,
        "cutoff_date": str(cutoff_date.date()),
        "train_start": str(train_df[DATE_COL].min().date()),
        "train_end": str(train_df[DATE_COL].max().date()),
        "test_start": str(test_df[DATE_COL].min().date()),
        "test_end": str(test_df[DATE_COL].max().date()),
        "total_rows": len(df),
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "valid_test_target_rows": len(valid_test),
        "rows_purged": rows_purged,
    }

    # Per-group breakdown
    for grp_key, grp in train_df.groupby(GROUP_COLS, sort=True):
        mkt, var, grade = grp_key
        if verbose:
            print(f"    Train | {mkt} | {var} | {grade}: {len(grp)} rows")

    return train_df, test_df, summary


def split_crop(crop: str, verbose: bool = True) -> dict:
    """Full pipeline: load features, compare targets, select, split, save."""
    if verbose:
        print(f"\n{'='*60}")
        print(f"TARGET SELECTION & SPLIT: {crop.upper()}")
        print(f"{'='*60}")

    fpath = FEATURES_PATHS[crop]
    if not fpath.exists():
        raise FileNotFoundError(f"Features file not found: {fpath}. Run multi_crop_feature_engineering.py first.")

    df = pd.read_csv(fpath, low_memory=False)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")

    if df.empty:
        if verbose:
            print(f"  WARNING: Empty features dataset for {crop}. Skipping split.")
        return {}

    # Target comparison
    target_comp = compare_targets(df)
    (OUTPUTS_DIR / "target_selection").mkdir(parents=True, exist_ok=True)
    target_comp.to_csv(TARGET_COMP_PATHS[crop], index=False)

    if verbose:
        print(f"\n  Target Comparison:")
        print(target_comp.to_string(index=False))

    primary_target = select_primary_target(df, crop)
    if verbose:
        print(f"\n  Selected Primary Target: {primary_target}")

    # Chronological split
    train_df, test_df, summary = chronological_split(df, primary_target, crop, verbose=verbose)

    if verbose:
        print(f"\n  Split Summary:")
        print(f"    Total rows        : {summary['total_rows']:,}")
        print(f"    Train rows        : {summary['train_rows']:,}")
        print(f"    Test rows         : {summary['test_rows']:,}")
        print(f"    Valid test targets: {summary['valid_test_target_rows']:,}")
        print(f"    Rows purged       : {summary['rows_purged']:,}")

    # Save outputs
    (OUTPUTS_DIR / "splits").mkdir(parents=True, exist_ok=True)
    TRAIN_OUTPUT_PATHS[crop].parent.mkdir(parents=True, exist_ok=True)

    train_df.to_csv(TRAIN_OUTPUT_PATHS[crop], index=False)
    test_df.to_csv(TEST_OUTPUT_PATHS[crop], index=False)
    pd.DataFrame([summary]).to_csv(SPLIT_SUMMARY_PATHS[crop], index=False)

    if verbose:
        print(f"\n  Saved train : {TRAIN_OUTPUT_PATHS[crop].relative_to(BASE_DIR)}")
        print(f"  Saved test  : {TEST_OUTPUT_PATHS[crop].relative_to(BASE_DIR)}")
        print(f"  Saved summary: {SPLIT_SUMMARY_PATHS[crop].relative_to(BASE_DIR)}")

    return {
        "crop": crop,
        "primary_target": primary_target,
        "train_df": train_df,
        "test_df": test_df,
        "summary": summary,
        "target_comparison": target_comp,
    }


def split_all_crops(verbose: bool = True) -> dict:
    """Split all three crops and return results dict."""
    results = {}
    for crop in ["Tomato", "Wheat", "Cotton"]:
        results[crop] = split_crop(crop, verbose=verbose)
    return results


if __name__ == "__main__":
    split_all_crops(verbose=True)
