"""
Data Loader module for MandiMitra ML pipeline.
Loads raw Agmarknet daily price CSV files, validates schemas,
combines them for Maharashtra (2024 - 2026), and outputs a combined CSV.
"""

from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd


def find_header_row(file_path: Path) -> int:
    """
    Detect the index of the header row in the CSV file.
    Agmarknet files often have a title banner in the first row.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for idx, line in enumerate(f):
            if idx > 10:
                break
            line_lower = line.lower()
            if "state" in line_lower and "market" in line_lower and "commodity" in line_lower:
                return idx
    return 0


def load_raw_csv_files(raw_dir: Path) -> Dict[str, pd.DataFrame]:
    """
    Find all CSV files in the raw data directory and load them.
    Prints metadata for each file.
    """
    csv_files = sorted(list(raw_dir.glob("*.csv")))
    if not csv_files:
        print(f"No CSV files found in {raw_dir}")
        return {}

    loaded_dfs = {}
    print("=" * 70)
    print(f"FOUND {len(csv_files)} CSV FILE(S) IN {raw_dir}")
    print("=" * 70)

    for file_path in csv_files:
        header_row = find_header_row(file_path)
        df = pd.read_csv(file_path, skiprows=header_row)
        
        # Clean column names by stripping whitespace
        df.columns = [str(c).strip() for c in df.columns]
        
        # Compute temporary date range for reporting if date column exists
        date_col = next((c for c in df.columns if "date" in c.lower()), None)
        date_range_str = "N/A"
        if date_col:
            temp_dates = pd.to_datetime(df[date_col], format="%d-%m-%Y", errors="coerce")
            valid_dates = temp_dates.dropna()
            if not valid_dates.empty:
                date_range_str = f"{valid_dates.min().strftime('%Y-%m-%d')} to {valid_dates.max().strftime('%Y-%m-%d')}"

        print(f"\nFilename: {file_path.name}")
        print(f"  - Number of rows   : {len(df):,}")
        print(f"  - Number of columns: {len(df.columns)}")
        print(f"  - Column names     : {list(df.columns)}")
        print(f"  - Date range       : {date_range_str}")

        loaded_dfs[file_path.name] = df

    return loaded_dfs


def check_column_compatibility(dfs_dict: Dict[str, pd.DataFrame]) -> Tuple[bool, List[str]]:
    """
    Check whether all DataFrames share the same column structure.
    """
    if not dfs_dict:
        return False, []

    first_file = next(iter(dfs_dict))
    base_columns = list(dfs_dict[first_file].columns)

    compatible = True
    print("\n" + "=" * 70)
    print("CHECKING COLUMN STRUCTURE COMPATIBILITY")
    print("=" * 70)

    for filename, df in dfs_dict.items():
        cols = list(df.columns)
        if cols != base_columns:
            compatible = False
            print(f"  [MISMATCH] {filename} columns differ from {first_file}:")
            print(f"     Expected: {base_columns}")
            print(f"     Found   : {cols}")
        else:
            print(f"  [OK] {filename} matches expected structure.")

    if compatible:
        print("\n=> All CSV files have IDENTICAL and COMPATIBLE column structures.")
    else:
        print("\n=> Schema mismatch detected across files.")

    return compatible, base_columns


def process_and_combine(
    dfs_dict: Dict[str, pd.DataFrame],
    target_state: str = "Maharashtra",
    start_date: str = "2024-01-01",
    end_date: str = "2026-12-31"
) -> pd.DataFrame:
    """
    Combines compatible files, parses dates, and filters by state and date range.
    Does NOT remove duplicates, clean text, or fill missing values.
    """
    combined_raw = pd.concat(dfs_dict.values(), ignore_index=True)

    # Locate Date and State columns
    date_col = next((c for c in combined_raw.columns if "date" in c.lower()), "Price Date")
    state_col = next((c for c in combined_raw.columns if "state" in c.lower()), "State/UT")

    # 6. Convert the date column to proper datetime format
    combined_raw[date_col] = pd.to_datetime(combined_raw[date_col], format="%d-%m-%Y", errors="coerce")

    # 7. Keep Maharashtra data only
    state_mask = combined_raw[state_col].astype(str).str.strip().str.lower() == target_state.lower()

    # 8. Keep data from 2024-01-01 through latest available date in 2026
    date_mask = (combined_raw[date_col] >= pd.to_datetime(start_date)) & (
        combined_raw[date_col] <= pd.to_datetime(end_date)
    )

    combined_filtered = combined_raw[state_mask & date_mask].copy()
    return combined_filtered


def print_dataset_summary(df: pd.DataFrame) -> None:
    """
    Prints the required statistics and diagnostics on the combined dataset.
    """
    date_col = next((c for c in df.columns if "date" in c.lower()), "Price Date")
    commodity_col = next((c for c in df.columns if "commodity" in c.lower() and "group" not in c.lower()), "Commodity")
    market_col = next((c for c in df.columns if "market" in c.lower()), "Market")

    print("\n" + "=" * 70)
    print("COMBINED DATASET SUMMARY & DIAGNOSTICS")
    print("=" * 70)

    # 10. Total number of rows
    print(f"Total number of rows: {len(df):,}")

    # 11. Date range
    if not df[date_col].dropna().empty:
        min_date = df[date_col].min().strftime("%Y-%m-%d")
        max_date = df[date_col].max().strftime("%Y-%m-%d")
        print(f"Date range: {min_date} to {max_date}")
    else:
        print("Date range: N/A (no valid dates found)")

    # 13. Number of unique markets
    if market_col in df.columns:
        unique_markets = df[market_col].dropna().unique()
        print(f"Number of unique markets: {len(unique_markets)}")
    else:
        print("Market column not found.")

    # 14. Number of unique commodities
    # 12. Print all unique commodities
    if commodity_col in df.columns:
        unique_commodities = sorted(df[commodity_col].dropna().astype(str).unique())
        print(f"Number of unique commodities: {len(unique_commodities)}")
        print(f"All unique commodities: {unique_commodities}")
    else:
        print("Commodity column not found.")

    # Columns
    print(f"Available columns ({len(df.columns)}): {list(df.columns)}")

    # 15. Missing-value counts
    print("\nMissing-value counts per column:")
    null_counts = df.isnull().sum()
    for col, val in null_counts.items():
        print(f"  - {col}: {val:,} missing ({val / len(df) * 100:.2f}%)")

    # 16. Duplicate-row count
    duplicate_count = df.duplicated().sum()
    print(f"\nDuplicate-row count: {duplicate_count:,} duplicate rows")
    print("=" * 70)


def main():
    base_dir = Path(__file__).resolve().parent.parent
    raw_dir = base_dir / "data" / "raw"
    processed_dir = base_dir / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_file = processed_dir / "maharashtra_2024_2026_combined.csv"

    # Step 1-3: Load raw CSV files and print file-level info
    dfs_dict = load_raw_csv_files(raw_dir)
    if not dfs_dict:
        return

    # Step 4: Check compatibility
    compatible, _ = check_column_compatibility(dfs_dict)
    if not compatible:
        print("Warning: Column incompatibility detected among CSV files.")

    # Step 5-8: Combine, parse dates, filter Maharashtra 2024-2026
    combined_df = process_and_combine(dfs_dict)

    # Step 10-16: Print detailed summary and diagnostics
    print_dataset_summary(combined_df)

    # Save the combined dataset
    combined_df.to_csv(output_file, index=False)
    print(f"\nSuccessfully saved combined dataset to:\n  {output_file}")


if __name__ == "__main__":
    main()
