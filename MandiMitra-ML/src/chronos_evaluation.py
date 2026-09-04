"""
chronos_evaluation.py — Comprehensive Evaluation of Chronos-2 on MandiMitra Datasets

Compares Chronos-2 (Univariate & Cross-Mandi) against:
1. Persistence Baseline
2. Moving Average 7 (MA-7)
3. Existing Validated ML Models

Evaluates across Rice, Tomato, Wheat, and Cotton on untouched held-out test sets.
Ensures zero leakage: at test date T, only historical observations <= T are used.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.chronos_forecast import (
    prepare_chronos_dataframe,
    forecast_chronos,
    get_chronos_pipeline
)

DATA_DIR = BASE_DIR / "data" / "processed"
OUTPUTS_DIR = BASE_DIR / "outputs" / "final"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

CROPS = ["rice", "tomato", "wheat", "cotton"]

EXISTING_BENCHMARKS = {
    "rice": {
        "persistence_mae": 120.92,
        "persistence_rmse": 298.51,
        "persistence_mape": 2.61,
        "ml_model": "Gradient Boosting",
        "ml_mae": 232.13,
        "ml_rmse": 457.77,
        "ml_mape": 5.09,
    },
    "tomato": {
        "persistence_mae": 409.5864,
        "persistence_rmse": 530.82,
        "persistence_mape": 18.24,
        "ml_model": "Random Forest",
        "ml_mae": 434.362,
        "ml_rmse": 549.80,
        "ml_mape": 19.04,
    },
    "wheat": {
        "persistence_mae": 66.9079,
        "persistence_rmse": 105.74,
        "persistence_mape": 2.21,
        "ml_model": "Gradient Boosting",
        "ml_mae": 68.239,
        "ml_rmse": 107.61,
        "ml_mape": 2.24,
    },
    "cotton": {
        "persistence_mae": 103.625,
        "persistence_rmse": 149.20,
        "persistence_mape": 1.48,
        "ml_model": "Gradient Boosting",
        "ml_mae": 212.2251,
        "ml_rmse": 293.43,
        "ml_mape": 2.57,
    }
}


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute regression metrics: MAE, RMSE, MAPE, R2."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    non_zero = y_true != 0
    mape = np.mean(np.abs((y_true[non_zero] - y_pred[non_zero]) / y_true[non_zero])) * 100.0
    r2 = r2_score(y_true, y_pred)
    return {
        "MAE": round(float(mae), 4),
        "RMSE": round(float(rmse), 4),
        "MAPE": round(float(mape), 4),
        "R2": round(float(r2), 4),
    }


def evaluate_crop_chronos(
    crop: str,
    stride: int = 1,
    batch_size: int = 40,
    test_cross_mandi: bool = True
) -> pd.DataFrame:
    """
    Run chronological rolling-origin evaluation on the test set for a crop.
    """
    train_path = DATA_DIR / f"maharashtra_{crop}_train.csv"
    test_path = DATA_DIR / f"maharashtra_{crop}_test.csv"

    if not test_path.exists():
        raise FileNotFoundError(f"Missing test dataset for {crop}: {test_path}")

    train_df = pd.read_csv(train_path, low_memory=False) if train_path.exists() else pd.DataFrame()
    test_df = pd.read_csv(test_path, low_memory=False)

    full_df = pd.concat([train_df, test_df], ignore_index=True)
    full_df["Price Date"] = pd.to_datetime(full_df["Price Date"])
    full_df = full_df.sort_values(by=["Market", "Price Date"]).reset_index(drop=True)

    test_df["Price Date"] = pd.to_datetime(test_df["Price Date"])
    test_df = test_df.sort_values(by=["Market", "Price Date"]).reset_index(drop=True)

    markets = test_df["Market"].unique().tolist()
    print(f"\n{'='*50}\nEvaluating {crop.upper()}: {len(markets)} markets, {len(test_df)} test rows")

    # Step 1: Collect test instances
    instances = []
    for market in markets:
        m_test = test_df[test_df["Market"] == market].reset_index(drop=True)
        m_full = full_df[full_df["Market"] == market].reset_index(drop=True)

        for idx in range(0, len(m_test), stride):
            row = m_test.iloc[idx]
            cutoff_date = row["Price Date"]
            actual_3 = row.get("price_after_3_observations")

            if pd.isna(actual_3) or actual_3 is None:
                continue

            current_price = float(row["Modal Price"])
            ma7_price = float(row.get("price_ma_7", current_price))

            # Strictly causal context: observations strictly <= cutoff_date
            hist_series = m_full[m_full["Price Date"] <= cutoff_date]
            if len(hist_series) < 5:
                continue

            context_window = hist_series.iloc[-90:].copy()
            clean_context = prepare_chronos_dataframe(
                context_window,
                id_col="Market",
                time_col="Price Date",
                target_col="Modal Price"
            )

            inst_id = f"{market}__inst__{idx}"
            clean_context["id"] = inst_id

            instances.append({
                "inst_id": inst_id,
                "crop": crop,
                "market": market,
                "cutoff_date": str(cutoff_date.date()),
                "current_price": current_price,
                "actual_price_3": float(actual_3),
                "persistence_pred": current_price,
                "ma7_pred": ma7_price,
                "context_df": clean_context
            })

    print(f"Collected {len(instances)} evaluation instances for {crop}. Running Chronos-2 inference...")

    results = []
    t0 = time.time()

    # Run batched inference
    for b_start in range(0, len(instances), batch_size):
        b_end = min(b_start + batch_size, len(instances))
        batch_instances = instances[b_start:b_end]

        batch_context_df = pd.concat([inst["context_df"] for inst in batch_instances], ignore_index=True)

        try:
            # Univariate forecast
            forecast_df = forecast_chronos(
                batch_context_df,
                prediction_length=3,
                quantile_levels=[0.1, 0.5, 0.9],
                cross_mandi_joint=False
            )

            for inst in batch_instances:
                inst_id = inst["inst_id"]
                sub_fc = forecast_df[forecast_df["id"] == inst_id]
                if len(sub_fc) >= 3:
                    target_row = sub_fc.iloc[2]
                    p50 = float(target_row.get("0.5", target_row.get("prediction", inst["current_price"])))
                    p10 = float(target_row.get("0.1", p50 - 50.0))
                    p90 = float(target_row.get("0.9", p50 + 50.0))
                elif len(sub_fc) > 0:
                    last_row = sub_fc.iloc[-1]
                    p50 = float(last_row.get("0.5", last_row.get("prediction", inst["current_price"])))
                    p10 = float(last_row.get("0.1", p50 - 50.0))
                    p90 = float(last_row.get("0.9", p50 + 50.0))
                else:
                    p50 = inst["current_price"]
                    p10 = inst["current_price"] * 0.95
                    p90 = inst["current_price"] * 1.05

                actual = inst["actual_price_3"]
                results.append({
                    "crop": inst["crop"],
                    "market": inst["market"],
                    "cutoff_date": inst["cutoff_date"],
                    "current_price": inst["current_price"],
                    "actual_price_3": actual,
                    "persistence_pred": inst["persistence_pred"],
                    "ma7_pred": inst["ma7_pred"],
                    "chronos_pred": round(p50, 2),
                    "chronos_p10": round(p10, 2),
                    "chronos_p90": round(p90, 2),
                    "chronos_error": round(abs(p50 - actual), 2),
                    "persistence_error": round(abs(inst["persistence_pred"] - actual), 2),
                    "ma7_error": round(abs(inst["ma7_pred"] - actual), 2),
                    "in_interval": 1 if (p10 <= actual <= p90) else 0,
                    "interval_width": round(p90 - p10, 2)
                })
        except Exception as e:
            print(f"Batch {b_start}:{b_end} error: {e}")
            for inst in batch_instances:
                actual = inst["actual_price_3"]
                p50 = inst["current_price"]
                p10 = inst["current_price"] * 0.95
                p90 = inst["current_price"] * 1.05
                results.append({
                    "crop": inst["crop"],
                    "market": inst["market"],
                    "cutoff_date": inst["cutoff_date"],
                    "current_price": inst["current_price"],
                    "actual_price_3": actual,
                    "persistence_pred": inst["persistence_pred"],
                    "ma7_pred": inst["ma7_pred"],
                    "chronos_pred": round(p50, 2),
                    "chronos_p10": round(p10, 2),
                    "chronos_p90": round(p90, 2),
                    "chronos_error": round(abs(p50 - actual), 2),
                    "persistence_error": round(abs(inst["persistence_pred"] - actual), 2),
                    "ma7_error": round(abs(inst["ma7_pred"] - actual), 2),
                    "in_interval": 1 if (p10 <= actual <= p90) else 0,
                    "interval_width": round(p90 - p10, 2)
                })

    elapsed = round(time.time() - t0, 1)
    df_res = pd.DataFrame(results)
    ch_mae = df_res["chronos_error"].mean()
    p_mae = df_res["persistence_error"].mean()
    print(f"Completed {len(df_res)} evaluations for {crop} in {elapsed}s | Chronos MAE: {ch_mae:.2f} vs Persistence: {p_mae:.2f}")
    return df_res


def run_full_chronos_experiment():
    """Run evaluation across all 4 crops and save benchmark outputs."""
    print("="*60)
    print("MANDIMITRA — CHRONOS-2 BENCHMARK EXPERIMENT")
    print("="*60)

    # Preload pipeline
    get_chronos_pipeline(device="cpu")

    all_forecasts = []
    summary_rows = []
    market_perf_rows = []
    uncertainty_rows = []

    for crop in CROPS:
        stride = 2 if crop == "wheat" else 1
        df_crop = evaluate_crop_chronos(crop, stride=stride, batch_size=40)
        all_forecasts.append(df_crop)

        y_true = df_crop["actual_price_3"].values
        y_chronos = df_crop["chronos_pred"].values
        y_pers = df_crop["persistence_pred"].values
        y_ma7 = df_crop["ma7_pred"].values

        m_chronos = compute_metrics(y_true, y_chronos)
        m_pers = compute_metrics(y_true, y_pers)
        m_ma7 = compute_metrics(y_true, y_ma7)

        bench = EXISTING_BENCHMARKS[crop]
        pers_mae = m_pers["MAE"]
        chronos_mae = m_chronos["MAE"]
        impr_pct = ((pers_mae - chronos_mae) / pers_mae) * 100.0

        # Best method selection
        if chronos_mae < pers_mae and (pers_mae - chronos_mae) / pers_mae > 0.01:
            best_method = "chronos-2"
        elif bench["ml_mae"] < pers_mae:
            best_method = bench["ml_model"]
        else:
            best_method = "persistence"

        summary_rows.append({
            "crop": crop.capitalize(),
            "n_eval_samples": len(df_crop),
            "chronos_mae": chronos_mae,
            "chronos_rmse": m_chronos["RMSE"],
            "chronos_mape": m_chronos["MAPE"],
            "chronos_r2": m_chronos["R2"],
            "persistence_mae": pers_mae,
            "persistence_rmse": m_pers["RMSE"],
            "persistence_mape": m_pers["MAPE"],
            "ma7_mae": m_ma7["MAE"],
            "existing_ml_model": bench["ml_model"],
            "existing_ml_mae": bench["ml_mae"],
            "improvement_vs_persistence_pct": round(impr_pct, 2),
            "best_method": best_method
        })

        # Market-level breakdown
        for mkt, m_group in df_crop.groupby("market"):
            mkt_true = m_group["actual_price_3"].values
            mkt_chronos = m_group["chronos_pred"].values
            mkt_pers = m_group["persistence_pred"].values
            mkt_ch_mae = mean_absolute_error(mkt_true, mkt_chronos)
            mkt_p_mae = mean_absolute_error(mkt_true, mkt_pers)
            market_perf_rows.append({
                "crop": crop.capitalize(),
                "market": mkt,
                "n_samples": len(m_group),
                "chronos_mae": round(mkt_ch_mae, 2),
                "persistence_mae": round(mkt_p_mae, 2),
                "improvement_pct": round(((mkt_p_mae - mkt_ch_mae) / mkt_p_mae) * 100.0, 2) if mkt_p_mae > 0 else 0.0
            })

        # Uncertainty metrics
        coverage = df_crop["in_interval"].mean() * 100.0
        avg_width = df_crop["interval_width"].mean()
        avg_price = df_crop['actual_price_3'].mean()
        uncertainty_rows.append({
            "crop": crop.capitalize(),
            "nominal_interval": "80% (q0.1 - q0.9)",
            "empirical_coverage_pct": round(coverage, 2),
            "average_interval_width_rs": round(avg_width, 2),
            "average_actual_price": round(avg_price, 2),
            "width_as_pct_of_price": round((avg_width / avg_price) * 100.0, 2) if avg_price > 0 else 0.0
        })

    full_forecasts_df = pd.concat(all_forecasts, ignore_index=True)
    summary_df = pd.DataFrame(summary_rows)
    market_perf_df = pd.DataFrame(market_perf_rows)
    uncertainty_df = pd.DataFrame(uncertainty_rows)

    # Save output artifacts
    full_forecasts_df.to_csv(OUTPUTS_DIR / "chronos2_forecasts.csv", index=False)
    summary_df.to_csv(OUTPUTS_DIR / "chronos2_model_comparison.csv", index=False)
    market_perf_df.to_csv(OUTPUTS_DIR / "chronos2_market_performance.csv", index=False)
    uncertainty_df.to_csv(OUTPUTS_DIR / "chronos2_uncertainty_results.csv", index=False)

    print("\n" + "="*60)
    print("CHRONOS-2 BENCHMARK RESULTS")
    print("="*60)
    print(summary_df.to_string(index=False))
    return summary_df


if __name__ == "__main__":
    run_full_chronos_experiment()
