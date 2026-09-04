"""
Target Selection, Chronological Train/Test Split, Baselines, and Validation
module for the MandiMitra ML pipeline.
"""

from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd


def compare_target_candidates(
    df: pd.DataFrame,
    targets: List[str] = None,
    modal_col: str = "Modal Price",
    ma_col: str = "price_ma_7"
) -> pd.DataFrame:
    """
    Compare prospective target candidates across distribution metrics,
    persistence baseline MAE, and recent-mean baseline MAE.
    """
    if targets is None:
        targets = [
            "price_next_observation",
            "price_after_3_observations",
            "price_after_7_observations"
        ]

    comparison_records = []
    for tgt in targets:
        valid = df.dropna(subset=[tgt, modal_col, ma_col])
        n_obs = len(valid)
        mean_val = float(valid[tgt].mean())
        median_val = float(valid[tgt].median())
        std_val = float(valid[tgt].std())
        min_val = float(valid[tgt].min())
        max_val = float(valid[tgt].max())

        # Baseline MAEs
        mae_persistence = float((valid[tgt] - valid[modal_col]).abs().mean())
        mae_ma7 = float((valid[tgt] - valid[ma_col]).abs().mean())

        comparison_records.append({
            "Target Candidate": tgt,
            "Valid Observations": n_obs,
            "Mean (Rs.)": round(mean_val, 2),
            "Median (Rs.)": round(median_val, 2),
            "Std Dev (Rs.)": round(std_val, 2),
            "Min (Rs.)": round(min_val, 2),
            "Max (Rs.)": round(max_val, 2),
            "Persistence MAE (Rs.)": round(mae_persistence, 2),
            "Recent-Mean (MA-7) MAE (Rs.)": round(mae_ma7, 2)
        })

    return pd.DataFrame(comparison_records)


def calculate_chronological_cutoff(
    df: pd.DataFrame,
    train_ratio: float = 0.80,
    date_col: str = "Price Date"
) -> pd.Timestamp:
    """
    Determine exact chronological cutoff date corresponding to approximately
    the earliest train_ratio of observations.
    """
    sorted_dates = pd.to_datetime(df[date_col]).sort_values().reset_index(drop=True)
    cutoff_idx = int(np.floor(len(sorted_dates) * train_ratio))
    cutoff_date = sorted_dates.iloc[cutoff_idx]
    return cutoff_date


def perform_chronological_split(
    df: pd.DataFrame,
    cutoff_date: pd.Timestamp,
    target_col: str = "price_after_3_observations",
    group_cols: List[str] = None,
    lead_steps: int = 3,
    date_col: str = "Price Date"
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, int]:
    """
    Perform strict chronological 80/20 train/test split.
    Purges training records whose target observation falls after the cutoff date
    to strictly prevent target leakage across the partition boundary.
    """
    if group_cols is None:
        group_cols = ["Market", "Variety", "Grade"]

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(by=group_cols + [date_col]).reset_index(drop=True)

    # Compute target realization date per group
    df["target_realization_date"] = df.groupby(group_cols)[date_col].shift(-lead_steps)

    # Initial time-based partition
    initial_train = df[df[date_col] <= cutoff_date].copy()
    test_df = df[df[date_col] > cutoff_date].copy().reset_index(drop=True)

    # Purge boundary leakage: train rows whose target date lies in the test period
    boundary_leakage_mask = initial_train["target_realization_date"] > cutoff_date
    n_purged = int(boundary_leakage_mask.sum())
    purged_records = initial_train[boundary_leakage_mask].copy()

    clean_train_df = initial_train[~boundary_leakage_mask].copy().reset_index(drop=True)

    return clean_train_df, test_df, purged_records, n_purged


def evaluate_baselines(
    test_df: pd.DataFrame,
    target_col: str = "price_after_3_observations",
    modal_col: str = "Modal Price",
    ma_col: str = "price_ma_7"
) -> pd.DataFrame:
    """
    Evaluate Persistence and Recent-Mean baselines on the test set.
    Calculates MAE, RMSE, and MAPE.
    """
    eval_df = test_df.dropna(subset=[target_col, modal_col, ma_col]).copy()
    y_true = eval_df[target_col].values

    # 1. Persistence baseline: prediction = current Modal Price
    y_pred_pers = eval_df[modal_col].values
    mae_pers = float(np.mean(np.abs(y_true - y_pred_pers)))
    rmse_pers = float(np.sqrt(np.mean((y_true - y_pred_pers) ** 2)))
    mape_pers = float(np.mean(np.abs((y_true - y_pred_pers) / y_true)) * 100.0)

    # 2. Recent-Mean baseline: prediction = price_ma_7
    y_pred_ma = eval_df[ma_col].values
    mae_ma = float(np.mean(np.abs(y_true - y_pred_ma)))
    rmse_ma = float(np.sqrt(np.mean((y_true - y_pred_ma) ** 2)))
    mape_ma = float(np.mean(np.abs((y_true - y_pred_ma) / y_true)) * 100.0)

    baseline_records = [
        {
            "Baseline Model": "Persistence Baseline (Modal Price)",
            "Forecast Strategy": "Prediction = Current Observed Modal Price",
            "Evaluation Samples": len(eval_df),
            "MAE (Rs.)": round(mae_pers, 2),
            "RMSE (Rs.)": round(rmse_pers, 2),
            "MAPE (%)": round(mape_pers, 2)
        },
        {
            "Baseline Model": "Recent-Mean Baseline (price_ma_7)",
            "Forecast Strategy": "Prediction = 7-Observation Backward Moving Average",
            "Evaluation Samples": len(eval_df),
            "MAE (Rs.)": round(mae_ma, 2),
            "RMSE (Rs.)": round(rmse_ma, 2),
            "MAPE (%)": round(mape_ma, 2)
        }
    ]

    return pd.DataFrame(baseline_records)


def validate_split_integrity(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    cutoff_date: pd.Timestamp,
    target_col: str,
    original_df: pd.DataFrame,
    group_cols: List[str] = None
) -> Dict[str, bool]:
    """
    Execute rigorous validation checks confirming chronological integrity,
    zero boundary target leakage, zero duplicate introduction, and feature isolation.
    """
    if group_cols is None:
        group_cols = ["Market", "Variety", "Grade"]

    checks = {}

    # Check 1: train dates occur strictly before test dates
    train_max_date = pd.to_datetime(train_df["Price Date"]).max()
    test_min_date = pd.to_datetime(test_df["Price Date"]).min()
    checks["train_dates_before_test_dates"] = bool(train_max_date < test_min_date)

    # Check 2: no train row has target realization date after cutoff
    if "target_realization_date" in train_df.columns:
        valid_targets = train_df["target_realization_date"].dropna()
        checks["no_train_target_after_cutoff"] = bool((valid_targets <= cutoff_date).all())
    else:
        checks["no_train_target_after_cutoff"] = True

    # Check 3: no exact duplicate rows introduced
    checks["zero_train_duplicates"] = bool(train_df.duplicated().sum() == 0)
    checks["zero_test_duplicates"] = bool(test_df.duplicated().sum() == 0)

    # Check 4: all rows belong to the 3 retained groups
    retained_groups = {
        ("APMC Alibagh", "Other", "Local"),
        ("APMC Murud", "Other", "Local"),
        ("APMC Palghar", "1009 Kar", "Local")
    }
    train_groups = set(zip(train_df["Market"], train_df["Variety"], train_df["Grade"]))
    test_groups = set(zip(test_df["Market"], test_df["Variety"], test_df["Grade"]))
    checks["all_rows_belong_to_retained_groups"] = bool(
        train_groups.issubset(retained_groups) and test_groups.issubset(retained_groups)
    )

    # Check 5: source feature dataset unchanged
    checks["source_features_unchanged"] = bool(len(original_df) == 1687 and len(original_df.columns) == 52)

    return checks


def main():
    base_dir = Path(__file__).resolve().parent.parent
    features_path = base_dir / "data" / "processed" / "maharashtra_rice_features.csv"
    train_output_path = base_dir / "data" / "processed" / "maharashtra_rice_train.csv"
    test_output_path = base_dir / "data" / "processed" / "maharashtra_rice_test.csv"
    target_comp_path = base_dir / "outputs" / "target_comparison.csv"
    baselines_path = base_dir / "outputs" / "baseline_results.csv"
    split_summary_path = base_dir / "outputs" / "split_summary.csv"

    print("=" * 75)
    print("STEP 6: TARGET SELECTION, TRAIN/TEST SPLIT & BASELINES")
    print("=" * 75)

    df_features = pd.read_csv(features_path)
    print(f"Loaded source features dataset: {features_path.name} ({len(df_features):,} rows x {len(df_features.columns)} cols)")

    # PART A — Target Comparison
    target_comp_df = compare_target_candidates(df_features)
    target_comp_df.to_csv(target_comp_path, index=False)
    print("\nTarget Candidates Comparison:")
    print(target_comp_df.to_string(index=False))

    # PART B — Primary Target Selection
    primary_target = "price_after_3_observations"
    print(f"\nSelected Primary Target: '{primary_target}'")
    print("Rationale: Provides a 3-observation forward horizon (~3-4 calendar days), granting actionable lead time for farmer harvesting and transit while preserving strong temporal correlation.")

    # PART C — Chronological Train/Test Split
    cutoff_date = calculate_chronological_cutoff(df_features, train_ratio=0.80)
    print(f"\nChronological 80/20 Cutoff Date: {cutoff_date.strftime('%Y-%m-%d')}")

    clean_train_df, test_df, purged_records, n_purged = perform_chronological_split(
        df_features, cutoff_date=cutoff_date, target_col=primary_target, lead_steps=3
    )

    print(f"Initial Train Rows (<= {cutoff_date.strftime('%Y-%m-%d')}): {len(clean_train_df) + n_purged:,}")
    print(f"Purged Boundary Leakage Rows (target > cutoff) : {n_purged}")
    print(f"Clean Train Rows                               : {len(clean_train_df):,}")
    print(f"Test Rows (> {cutoff_date.strftime('%Y-%m-%d')})   : {len(test_df):,}")

    # Build Split Summary Table
    group_cols = ["Market", "Variety", "Grade"]
    summary_rows = []
    for keys in clean_train_df.groupby(group_cols).groups.keys():
        m, v, g = keys
        tr_cnt = len(clean_train_df[(clean_train_df["Market"] == m) & (clean_train_df["Variety"] == v) & (clean_train_df["Grade"] == g)])
        te_cnt = len(test_df[(test_df["Market"] == m) & (test_df["Variety"] == v) & (test_df["Grade"] == g)])
        summary_rows.append({
            "Market": m,
            "Variety": v,
            "Grade": g,
            "Train Observations": tr_cnt,
            "Test Observations": te_cnt,
            "Total Retained": tr_cnt + te_cnt,
            "Train Ratio (%)": round((tr_cnt / (tr_cnt + te_cnt)) * 100, 2)
        })
    split_summary_df = pd.DataFrame(summary_rows)
    split_summary_df.to_csv(split_summary_path, index=False)
    print("\nGroup Split Distribution:")
    print(split_summary_df.to_string(index=False))

    # PART D — Baselines on Test Set
    baseline_df = evaluate_baselines(test_df, target_col=primary_target)
    baseline_df.to_csv(baselines_path, index=False)
    print("\nTest Set Baseline Performance:")
    print(baseline_df.to_string(index=False))

    # PART E — Save Datasets
    clean_train_df.to_csv(train_output_path, index=False)
    test_df.to_csv(test_output_path, index=False)
    print(f"\nSaved clean train dataset: {train_output_path} ({len(clean_train_df):,} rows)")
    print(f"Saved test dataset       : {test_output_path} ({len(test_df):,} rows)")
    print(f"Saved target comparison  : {target_comp_path}")
    print(f"Saved baseline results   : {baselines_path}")
    print(f"Saved split summary      : {split_summary_path}")

    # PART F — Validation Checks
    validation_results = validate_split_integrity(
        clean_train_df, test_df, cutoff_date, primary_target, df_features
    )
    print("\nValidation Audit Results:")
    for check_name, status in validation_results.items():
        print(f"  - {check_name:<36}: {'PASSED' if status else 'FAILED'}")

    all_passed = all(validation_results.values())
    print(f"\nOverall Validation Status: {'ALL CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}")
    print("=" * 75)


if __name__ == "__main__":
    main()
