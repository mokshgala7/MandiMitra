"""
Multi-Crop Data Cleaning for MandiMitra ML Pipeline.
Applies the >=500 observation filter independently per crop and produces
clean modeling datasets.  Rice files are not touched.
"""

from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUTS_DIR = BASE_DIR / "outputs"

COMBINED_PATHS = {
    "Tomato": PROCESSED_DIR / "maharashtra_tomato_2024_2026_combined.csv",
    "Wheat": PROCESSED_DIR / "maharashtra_wheat_2024_2026_combined.csv",
    "Cotton": PROCESSED_DIR / "maharashtra_cotton_2024_2026_combined.csv",
}
MODELING_OUTPUT_PATHS = {
    "Tomato": PROCESSED_DIR / "maharashtra_tomato_modeling_clean.csv",
    "Wheat": PROCESSED_DIR / "maharashtra_wheat_modeling_clean.csv",
    "Cotton": PROCESSED_DIR / "maharashtra_cotton_modeling_clean.csv",
}
COVERAGE_OUTPUT_PATHS = {
    "Tomato": OUTPUTS_DIR / "coverage" / "tomato_market_coverage.csv",
    "Wheat": OUTPUTS_DIR / "coverage" / "wheat_market_coverage.csv",
    "Cotton": OUTPUTS_DIR / "coverage" / "cotton_market_coverage.csv",
}
CLEANING_SUMMARY_PATHS = {
    "Tomato": OUTPUTS_DIR / "cleaning" / "tomato_cleaning_summary.csv",
    "Wheat": OUTPUTS_DIR / "cleaning" / "wheat_cleaning_summary.csv",
    "Cotton": OUTPUTS_DIR / "cleaning" / "cotton_cleaning_summary.csv",
}

MIN_OBS_THRESHOLD = 500
# Cotton is a seasonal crop — no group reaches 500 obs (highest = 412).
# An adaptive threshold of 300 is applied for Cotton only, clearly documented.
CROP_OBS_THRESHOLDS = {
    "Tomato": 500,
    "Wheat": 500,
    "Cotton": 300,  # Adaptive: seasonal crop, max group = 412 obs (APMC Hinganghat)
}
DATE_COL = "Price Date"
GROUP_COLS = ["Market", "Variety", "Grade"]
NUMERIC_COLS = ["Min Price", "Max Price", "Modal Price"]


def _strip_numeric(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
        .replace("nan", np.nan)
        .astype(float)
    )


def load_combined(crop: str) -> pd.DataFrame:
    path = COMBINED_PATHS[crop]
    if not path.exists():
        raise FileNotFoundError(f"Combined CSV not found: {path}. Run multi_crop_data_loader.py first.")
    df = pd.read_csv(path, low_memory=False)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
    for col in NUMERIC_COLS:
        df[col] = _strip_numeric(df[col])
    return df


def build_coverage_report(crop: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Build Market + Variety + Grade coverage report with retention flag.
    """
    total_calendar_days = (df[DATE_COL].max() - df[DATE_COL].min()).days + 1
    rows = []
    for (mkt, var, grade), grp in df.groupby(GROUP_COLS, sort=True):
        grp = grp.sort_values(DATE_COL)
        obs_count = len(grp)
        first_date = grp[DATE_COL].min()
        last_date = grp[DATE_COL].max()
        calendar_span = (last_date - first_date).days + 1
        coverage_pct = round(obs_count / max(calendar_span, 1) * 100, 2)

        # Max consecutive gap in calendar days between successive observations
        date_diffs = grp[DATE_COL].diff().dt.days.dropna()
        max_gap = int(date_diffs.max()) if len(date_diffs) > 0 else 0

        rows.append({
            "Market": mkt,
            "Variety": var,
            "Grade": grade,
            "Observation_Count": obs_count,
            "First_Date": str(first_date.date()),
            "Last_Date": str(last_date.date()),
            "Calendar_Span_Days": calendar_span,
            "Coverage_Pct": coverage_pct,
            "Max_Consecutive_Gap_Days": max_gap,
            "Retained": obs_count >= MIN_OBS_THRESHOLD,
        })

    report = pd.DataFrame(rows).sort_values("Observation_Count", ascending=False).reset_index(drop=True)
    return report


def clean_crop(crop: str, verbose: bool = True, threshold: int = None) -> tuple:
    """
    Load combined data, build coverage report, filter to retained groups,
    clean, flag outliers, save outputs.
    Returns (clean_df, coverage_df, summary_dict).
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"CLEANING: {crop.upper()}")
        print(f"{'='*60}")

    # Determine effective threshold for this crop
    effective_threshold = threshold if threshold is not None else CROP_OBS_THRESHOLDS.get(crop, MIN_OBS_THRESHOLD)

    df = load_combined(crop)
    raw_rows = len(df)
    if verbose:
        print(f"  Loaded: {raw_rows:,} rows")
        if effective_threshold != MIN_OBS_THRESHOLD:
            print(f"  NOTE: Using adaptive threshold of {effective_threshold} obs for {crop} "
                  f"(seasonal crop; no group reaches {MIN_OBS_THRESHOLD}).")

    # --- Step A: Remove exact duplicates ---
    before_dedup = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    exact_dups_removed = before_dedup - len(df)
    if verbose and exact_dups_removed:
        print(f"  Removed {exact_dups_removed} exact duplicate rows.")

    # --- Step B: Build coverage report using effective threshold ---
    # build_coverage_report always marks Retained using MIN_OBS_THRESHOLD=500 for auditability.
    # We then apply the per-crop effective_threshold for actual filtering.
    coverage_df = build_coverage_report(crop, df)
    # Override Retained flag with effective threshold
    coverage_df["Retained"] = coverage_df["Observation_Count"] >= effective_threshold
    retained_groups = coverage_df[coverage_df["Retained"]].copy()
    excluded_count = int((~coverage_df["Retained"]).sum())
    retained_count = int(coverage_df["Retained"].sum())

    if verbose:
        print(f"  Total Market+Variety+Grade groups : {len(coverage_df)}")
        print(f"  Retained (>={effective_threshold} obs): {retained_count}")
        print(f"  Excluded (<{effective_threshold} obs): {excluded_count}")
        if retained_count > 0:
            print(f"  Retained groups:")
            for _, row in retained_groups.iterrows():
                print(f"    {row['Market']} | {row['Variety']} | {row['Grade']} — {row['Observation_Count']} obs")

    # --- Step C: Filter to retained groups ---
    retained_keys = set(
        zip(retained_groups["Market"], retained_groups["Variety"], retained_groups["Grade"])
    )
    mask = df.apply(
        lambda r: (r["Market"], r["Variety"], r["Grade"]) in retained_keys, axis=1
    )
    clean_df = df[mask].copy()
    rows_after_filter = len(clean_df)

    # --- Step D: Sort chronologically within each series ---
    clean_df = clean_df.sort_values([DATE_COL, "Market", "Variety", "Grade"]).reset_index(drop=True)

    # --- Step E: Verify Min <= Modal <= Max and flag violations ---
    violation_mask = (
        (clean_df["Min Price"] > clean_df["Modal Price"]) |
        (clean_df["Modal Price"] > clean_df["Max Price"])
    )
    price_violations = violation_mask.sum()
    clean_df["price_order_flag"] = violation_mask.astype(int)
    if verbose:
        print(f"  Price order violations (Min>Modal or Modal>Max): {price_violations}")

    # --- Step F: Flag statistical outliers (IQR×3) per group without removing ---
    outlier_flags = []
    for (mkt, var, grade), grp in clean_df.groupby(GROUP_COLS, sort=False):
        modal = grp["Modal Price"]
        q1, q3 = modal.quantile(0.25), modal.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 3 * iqr, q3 + 3 * iqr
        outlier_flags.extend((modal < lower) | (modal > upper))
    clean_df["statistical_outlier_flag"] = [int(f) for f in outlier_flags]

    if verbose:
        print(f"  Statistical outlier flags (IQR×3): {clean_df['statistical_outlier_flag'].sum()}")
        print(f"  Modeling rows retained: {rows_after_filter:,}")

    # --- Save outputs ---
    (OUTPUTS_DIR / "coverage").mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "cleaning").mkdir(parents=True, exist_ok=True)

    coverage_df.to_csv(COVERAGE_OUTPUT_PATHS[crop], index=False)
    clean_df.to_csv(MODELING_OUTPUT_PATHS[crop], index=False)

    summary = {
        "crop": crop,
        "obs_threshold_used": effective_threshold,
        "threshold_note": f"Adaptive {effective_threshold}" if effective_threshold != MIN_OBS_THRESHOLD else f"Standard {MIN_OBS_THRESHOLD}",
        "raw_rows": raw_rows,
        "exact_dups_removed": exact_dups_removed,
        "total_groups": len(coverage_df),
        "retained_groups": int(retained_count),
        "excluded_groups": int(excluded_count),
        "modeling_rows": rows_after_filter,
        "price_violations": int(price_violations),
        "statistical_outlier_flags": int(clean_df["statistical_outlier_flag"].sum()),
    }
    pd.DataFrame([summary]).to_csv(CLEANING_SUMMARY_PATHS[crop], index=False)

    if verbose:
        print(f"  Saved coverage report: {COVERAGE_OUTPUT_PATHS[crop].relative_to(BASE_DIR)}")
        print(f"  Saved modeling clean : {MODELING_OUTPUT_PATHS[crop].relative_to(BASE_DIR)}")
        print(f"  Saved cleaning summary: {CLEANING_SUMMARY_PATHS[crop].relative_to(BASE_DIR)}")

    return clean_df, coverage_df, summary


def clean_all_crops(verbose: bool = True) -> dict:
    """Clean all three crops and return results dict."""
    results = {}
    for crop in ["Tomato", "Wheat", "Cotton"]:
        clean_df, coverage_df, summary = clean_crop(crop, verbose=verbose)
        results[crop] = {"clean_df": clean_df, "coverage_df": coverage_df, "summary": summary}
    return results


if __name__ == "__main__":
    clean_all_crops(verbose=True)
