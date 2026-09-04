"""
Multi-Crop Data Loader for MandiMitra ML Pipeline.
Loads and combines raw AGMARKNET CSV files for Tomato, Wheat, and Cotton.
Schema is identical to Rice: 12 standard AGMARKNET columns.
Rice files in data/raw/ are completely ignored.
"""

from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUTS_DIR = BASE_DIR / "outputs"

CROP_FILES = {
    "Tomato": ["tomato2024.csv", "tomato2025.csv", "tomato2026.csv"],
    "Wheat": ["wheat2024.csv", "wheat2025.csv", "wheat2026.csv"],
    "Cotton": ["cotton2024.csv", "cotton2025.csv", "cotton2026.csv"],
}

EXPECTED_COLUMNS = [
    "State/UT", "District", "Market", "Commodity Group",
    "Commodity", "Variety", "Grade",
    "Min Price", "Max Price", "Modal Price",
    "Price Unit", "Price Date"
]

NUMERIC_COLS = ["Min Price", "Max Price", "Modal Price"]
DATE_COL = "Price Date"
COMBINED_OUTPUT_NAMES = {
    "Tomato": "maharashtra_tomato_2024_2026_combined.csv",
    "Wheat": "maharashtra_wheat_2024_2026_combined.csv",
    "Cotton": "maharashtra_cotton_2024_2026_combined.csv",
}
VALIDATION_OUTPUT_NAMES = {
    "Tomato": "tomato_data_validation.csv",
    "Wheat": "wheat_data_validation.csv",
    "Cotton": "cotton_data_validation.csv",
}


def _strip_numeric(series: pd.Series) -> pd.Series:
    """Remove thousands-commas and cast to float."""
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
        .replace("nan", np.nan)
        .astype(float)
    )


def load_single_file(filepath: Path) -> pd.DataFrame:
    """Load one AGMARKNET CSV, skip the banner header row, return clean DataFrame."""
    df = pd.read_csv(filepath, skiprows=1, encoding="utf-8", low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    # Drop any fully-blank rows from formatting artefacts
    df = df.dropna(how="all").reset_index(drop=True)
    # Strip whitespace from string columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()
    return df


def parse_and_validate(df: pd.DataFrame, filepath: Path) -> pd.DataFrame:
    """Parse numeric/date columns, verify schema, return validated DataFrame."""
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{filepath.name}: Missing columns {missing}. Found: {list(df.columns)}")

    for col in NUMERIC_COLS:
        df[col] = _strip_numeric(df[col])

    df[DATE_COL] = pd.to_datetime(df[DATE_COL], dayfirst=True, errors="coerce")
    invalid_dates = df[DATE_COL].isna().sum()
    if invalid_dates > 0:
        print(f"  WARNING: {invalid_dates} invalid dates in {filepath.name} — dropped.")
        df = df.dropna(subset=[DATE_COL])

    return df


def load_and_combine_crop(crop: str, verbose: bool = True) -> pd.DataFrame:
    """Load, validate, and combine all year files for one crop."""
    if verbose:
        print(f"\n{'='*60}")
        print(f"CROP: {crop.upper()}")
        print(f"{'='*60}")

    frames = []
    for fname in CROP_FILES[crop]:
        fpath = RAW_DIR / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Expected file not found: {fpath}")
        raw = load_single_file(fpath)
        validated = parse_and_validate(raw, fpath)
        if verbose:
            print(f"  {fname}: {len(validated):,} rows | "
                  f"{validated[DATE_COL].min().date()} to {validated[DATE_COL].max().date()}")
        frames.append(validated)

    combined = pd.concat(frames, ignore_index=True)

    # Deduplicate within crop (identical rows from year-boundary overlaps)
    before_dedup = len(combined)
    combined = combined.drop_duplicates()
    dedup_dropped = before_dedup - len(combined)
    if dedup_dropped > 0 and verbose:
        print(f"  Dropped {dedup_dropped} exact duplicate rows during combine.")

    combined = combined.sort_values([DATE_COL, "Market", "Variety", "Grade"]).reset_index(drop=True)

    if verbose:
        print(f"  Combined total: {len(combined):,} rows | "
              f"{combined[DATE_COL].min().date()} to {combined[DATE_COL].max().date()}")
        print(f"  Unique markets: {combined['Market'].nunique()} | "
              f"Varieties: {combined['Variety'].nunique()} | "
              f"Grades: {combined['Grade'].nunique()}")
        print(f"  Missing values: {combined.isna().sum().sum()}")

    return combined


def validate_crop_df(crop: str, df: pd.DataFrame) -> dict:
    """Compute validation statistics for one crop combined DataFrame."""
    exact_dups = df.duplicated().sum()
    price_violations = (
        (df["Min Price"] > df["Modal Price"]) |
        (df["Modal Price"] > df["Max Price"])
    ).sum()

    return {
        "crop": crop,
        "rows": len(df),
        "columns": len(df.columns),
        "start_date": str(df[DATE_COL].min().date()),
        "end_date": str(df[DATE_COL].max().date()),
        "unique_markets": df["Market"].nunique(),
        "unique_varieties": df["Variety"].nunique(),
        "unique_grades": df["Grade"].nunique(),
        "unique_commodities": df["Commodity"].nunique(),
        "missing_values": int(df.isna().sum().sum()),
        "exact_duplicates": int(exact_dups),
        "min_modal_max_violations": int(price_violations),
    }


def save_combined(crop: str, df: pd.DataFrame) -> Path:
    """Save combined CSV to data/processed/."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / COMBINED_OUTPUT_NAMES[crop]
    df.to_csv(out_path, index=False)
    print(f"  Saved: {out_path.relative_to(BASE_DIR)}")
    return out_path


def save_validation_report(crop: str, stats: dict) -> Path:
    """Save per-crop validation report to outputs/."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUTS_DIR / VALIDATION_OUTPUT_NAMES[crop]
    pd.DataFrame([stats]).to_csv(out_path, index=False)
    print(f"  Saved validation: {out_path.relative_to(BASE_DIR)}")
    return out_path


def run_all_crops(verbose: bool = True) -> dict:
    """
    Main entry point: load, validate, save all three crops.
    Returns dict of {crop: (DataFrame, stats_dict)}.
    """
    all_results = {}
    summary_rows = []

    for crop in ["Tomato", "Wheat", "Cotton"]:
        combined_df = load_and_combine_crop(crop, verbose=verbose)
        stats = validate_crop_df(crop, combined_df)
        save_combined(crop, combined_df)
        save_validation_report(crop, stats)
        all_results[crop] = (combined_df, stats)
        summary_rows.append({
            "crop": crop,
            "rows": stats["rows"],
            "start_date": stats["start_date"],
            "end_date": stats["end_date"],
            "unique_markets": stats["unique_markets"],
            "unique_varieties": stats["unique_varieties"],
            "unique_grades": stats["unique_grades"],
            "missing_values": stats["missing_values"],
            "exact_duplicates": stats["exact_duplicates"],
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_path = OUTPUTS_DIR / "multi_crop_data_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    if verbose:
        print(f"\n{'='*60}")
        print("MULTI-CROP DATA SUMMARY")
        print(f"{'='*60}")
        print(summary_df.to_string(index=False))
        print(f"\nSaved summary: {summary_path.relative_to(BASE_DIR)}")

    return all_results


if __name__ == "__main__":
    run_all_crops(verbose=True)
