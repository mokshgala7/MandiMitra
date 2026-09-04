"""
Data Cleaning and Modeling Data Preparation module for MandiMitra.
Processes Maharashtra Rice daily mandi prices, performs validation,
handles exact duplicates, detects outliers, and filters high-coverage
market-variety-grade time series for machine learning.
"""

from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd


def load_dataset(file_path: Path) -> pd.DataFrame:
    """Load combined dataset without modifying the source file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found at {file_path}")
    df = pd.read_csv(file_path)
    print(f"Loaded dataset: {file_path.name} with {len(df):,} rows and {len(df.columns)} columns.")
    return df


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Strip leading/trailing whitespace from all column names."""
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    return df


def clean_string_values(df: pd.DataFrame) -> pd.DataFrame:
    """Strip leading/trailing whitespace from categorical string columns."""
    df = df.copy()
    string_cols = [
        "State/UT", "District", "Market", "Commodity Group",
        "Commodity", "Variety", "Grade", "Price Unit"
    ]
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df


def convert_price_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Convert Min Price, Max Price, and Modal Price from formatted strings to float.
    Correctly parses numbers containing commas (e.g. '4,500.00').
    Reports any non-convertible values.
    """
    df = df.copy()
    price_cols = ["Min Price", "Max Price", "Modal Price"]
    non_convertible = {}

    for col in price_cols:
        if col in df.columns:
            # Strip commas and whitespace
            cleaned_series = df[col].astype(str).str.replace(",", "", regex=False).str.strip()
            numeric_series = pd.to_numeric(cleaned_series, errors="coerce")
            
            n_nan = numeric_series.isna().sum()
            non_convertible[col] = int(n_nan)
            df[col] = numeric_series

    return df, non_convertible


def convert_date(df: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
    """
    Convert Price Date to pandas datetime and verify date range.
    Expected range: 2024-01-01 through 2026-09-03.
    """
    df = df.copy()
    df["Price Date"] = pd.to_datetime(df["Price Date"], format="%Y-%m-%d", errors="coerce")

    min_date = df["Price Date"].min()
    max_date = df["Price Date"].max()
    within_bounds = (min_date >= pd.to_datetime("2024-01-01")) and (max_date <= pd.to_datetime("2026-09-03"))

    return df, within_bounds


def check_price_consistency(df: pd.DataFrame) -> Tuple[int, float, pd.DataFrame]:
    """
    Verify the business rule: Min Price <= Modal Price <= Max Price.
    Returns count of violations, percentage, and violating rows.
    """
    violation_min = df["Min Price"] > df["Modal Price"]
    violation_max = df["Modal Price"] > df["Max Price"]
    violations = violation_min | violation_max

    n_violations = int(violations.sum())
    pct_violations = (n_violations / len(df)) * 100 if len(df) > 0 else 0.0
    violating_rows = df[violations]

    return n_violations, pct_violations, violating_rows


def investigate_and_remove_exact_duplicates(
    df: pd.DataFrame,
    key_cols: List[str] = None
) -> Tuple[pd.DataFrame, int, int]:
    """
    Investigate duplicates on Market + Variety + Grade + Price Date.
    Remove ONLY exact duplicate observations across all columns.
    """
    if key_cols is None:
        key_cols = ["Market", "Variety", "Grade", "Price Date"]

    df = df.copy()
    key_dups_count = int(df.duplicated(subset=key_cols, keep=False).sum())
    
    # Check exact row duplicates across all columns
    exact_dups = df.duplicated(keep="first")
    n_exact_removed = int(exact_dups.sum())

    # Filter out only exact duplicates
    cleaned_df = df[~exact_dups].copy()

    return cleaned_df, key_dups_count, n_exact_removed


def detect_outliers(
    df: pd.DataFrame,
    group_cols: List[str] = None
) -> Tuple[pd.DataFrame, int]:
    """
    Detect suspicious price observations using market-level robust statistics.
    Uses Tukey's IQR (1.5 * IQR) per group; if IQR == 0 (e.g. sticky prices),
    falls back to 3-sigma robust bound from mean.
    Creates outlier_flag (1 for outlier, 0 otherwise) without modifying prices.
    """
    if group_cols is None:
        group_cols = ["Market", "Variety", "Grade"]

    df = df.copy()
    df["outlier_flag"] = 0

    for _, group_indices in df.groupby(group_cols).groups.items():
        sub = df.loc[group_indices, "Modal Price"]
        if len(sub) < 5:
            continue

        q25 = sub.quantile(0.25)
        q75 = sub.quantile(0.75)
        iqr = q75 - q25

        if iqr > 0:
            lower = q25 - 1.5 * iqr
            upper = q75 + 1.5 * iqr
        else:
            mean = sub.mean()
            std = sub.std()
            lower = mean - 3 * std
            upper = mean + 3 * std

        outliers = (sub < lower) | (sub > upper)
        df.loc[group_indices[outliers], "outlier_flag"] = 1

    n_outliers = int(df["outlier_flag"].sum())
    return df, n_outliers


def evaluate_market_coverage(
    df: pd.DataFrame,
    min_observations: int = 500
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate observation counts for every Market + Variety + Grade.
    Retain only combinations with >= min_observations.
    """
    coverage = df.groupby(["Market", "Variety", "Grade"]).size().reset_index(name="Observation Count")
    coverage["Retained"] = coverage["Observation Count"] >= min_observations
    coverage = coverage.sort_values(by="Observation Count", ascending=False).reset_index(drop=True)

    retained_keys = coverage[coverage["Retained"]][["Market", "Variety", "Grade"]]
    modeling_df = df.merge(retained_keys, on=["Market", "Variety", "Grade"]).copy()

    return coverage, modeling_df


def sort_and_verify_time_series(
    modeling_df: pd.DataFrame,
    group_cols: List[str] = None
) -> pd.DataFrame:
    """
    Sort observations chronologically by Price Date within each retained group.
    """
    if group_cols is None:
        group_cols = ["Market", "Variety", "Grade"]

    sorted_df = modeling_df.sort_values(by=group_cols + ["Price Date"]).reset_index(drop=True)
    return sorted_df


def analyze_missing_dates(
    modeling_df: pd.DataFrame,
    group_cols: List[str] = None
) -> pd.DataFrame:
    """
    Document gaps and missing calendar days for each retained market series.
    Does NOT interpolate or fill missing dates.
    """
    if group_cols is None:
        group_cols = ["Market", "Variety", "Grade"]

    gap_records = []
    for keys, group in modeling_df.groupby(group_cols):
        dates = group["Price Date"].sort_values()
        n_obs = len(dates)
        start_d = dates.min()
        end_d = dates.max()
        span_days = (end_d - start_d).days + 1
        missing_days = span_days - n_obs
        diffs = dates.diff().dt.days
        max_gap = int(diffs.max()) if len(diffs) > 1 else 0

        gap_records.append({
            "Market": keys[0],
            "Variety": keys[1],
            "Grade": keys[2],
            "Start Date": start_d.strftime("%Y-%m-%d"),
            "End Date": end_d.strftime("%Y-%m-%d"),
            "Observed Days": n_obs,
            "Calendar Span": span_days,
            "Missing Days": missing_days,
            "Coverage Rate (%)": round((n_obs / span_days) * 100, 2),
            "Max Gap (Days)": max_gap
        })

    return pd.DataFrame(gap_records)


def main():
    base_dir = Path(__file__).resolve().parent.parent
    raw_combined_path = base_dir / "data" / "processed" / "maharashtra_2024_2026_combined.csv"
    clean_modeling_path = base_dir / "data" / "processed" / "maharashtra_rice_modeling_clean.csv"
    coverage_report_path = base_dir / "outputs" / "market_coverage_report.csv"
    coverage_report_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 75)
    print("STEP 4: DATA CLEANING & MODELING DATA PREPARATION")
    print("=" * 75)

    # 1. Load Data
    df_raw = load_dataset(raw_combined_path)
    orig_rows = len(df_raw)

    # 2. Clean Column Names
    df_clean = clean_column_names(df_raw)

    # 3. Clean String Values
    df_clean = clean_string_values(df_clean)

    # 4. Convert Price Columns
    df_clean, non_convertible = convert_price_columns(df_clean)
    print(f"Price conversion non-convertible counts: {non_convertible}")

    # 5. Convert Date
    df_clean, date_valid = convert_date(df_clean)
    print(f"Date conversion complete. Dates valid [2024-01-01 to 2026-09-03]: {date_valid}")

    # 6. Check Price Consistency
    n_violations, pct_violations, _ = check_price_consistency(df_clean)
    print(f"Price consistency violations (Min <= Modal <= Max): {n_violations} ({pct_violations:.2f}%)")

    # 7. Duplicates
    df_clean, key_dups, n_exact_removed = investigate_and_remove_exact_duplicates(df_clean)
    print(f"Key duplicates on [Market, Variety, Grade, Price Date]: {key_dups}")
    print(f"Exact duplicate rows removed: {n_exact_removed}")

    # 8. Outlier Detection
    df_clean, total_outliers = detect_outliers(df_clean)
    print(f"Outlier observations flagged across all data: {total_outliers}")

    # 9. Market/Variety/Grade Coverage (>= 500 threshold)
    coverage_report, modeling_df = evaluate_market_coverage(df_clean, min_observations=500)
    retained_groups_count = int(coverage_report["Retained"].sum())
    excluded_groups_count = len(coverage_report) - retained_groups_count
    coverage_report.to_csv(coverage_report_path, index=False)
    print(f"Saved market coverage report to: {coverage_report_path}")

    # 10. Sort Time Series
    modeling_df = sort_and_verify_time_series(modeling_df)

    # 11. Missing Dates Assessment
    gap_df = analyze_missing_dates(modeling_df)
    print("\nRetained Series Temporal Gap Analysis:")
    print(gap_df.to_string(index=False))

    # Outliers in retained modeling data
    modeling_outliers = int(modeling_df["outlier_flag"].sum())

    # 12. Save Clean Modeling Dataset
    modeling_df.to_csv(clean_modeling_path, index=False)
    print(f"\nSaved cleaned modeling dataset to:\n  {clean_modeling_path}")

    # 13. Final Report
    print("\n" + "=" * 75)
    print("STEP 4 CLEANING & FILTERING SUMMARY REPORT")
    print("=" * 75)
    print(f"Original row count                    : {orig_rows:,}")
    print(f"Final modeling row count              : {len(modeling_df):,}")
    print(f"Retained Market+Variety+Grade groups  : {retained_groups_count}")
    print(f"Excluded Market+Variety+Grade groups  : {excluded_groups_count}")
    print(f"Exact duplicates removed              : {n_exact_removed}")
    print(f"Outliers flagged in modeling dataset  : {modeling_outliers} (flagged, not removed)")
    print(f"Price consistency violations          : {n_violations}")
    print(f"Missing values after cleaning         : {modeling_df.isna().sum().sum()}")
    print(f"Date range of modeling dataset        : {modeling_df['Price Date'].min().strftime('%Y-%m-%d')} to {modeling_df['Price Date'].max().strftime('%Y-%m-%d')}")
    print(f"Number of retained markets            : {modeling_df['Market'].nunique()}")
    print(f"Number of retained varieties          : {modeling_df['Variety'].nunique()}")
    print(f"Number of retained grades             : {modeling_df['Grade'].nunique()}")
    print("\nRetained Groups Detail:")
    retained_table = coverage_report[coverage_report["Retained"]][["Market", "Variety", "Grade", "Observation Count"]]
    print(retained_table.to_string(index=False))
    print("=" * 75)


if __name__ == "__main__":
    main()
