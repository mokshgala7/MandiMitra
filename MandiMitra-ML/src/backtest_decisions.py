"""
backtest_decisions.py — MandiMitra Decision Backtest

Simulates historical SELL/WAIT decisions using ONLY information available
at each prediction point. Never uses future information to generate a decision.

For each test-set row per crop:
    1. Use current_price (Modal Price) and historical features known at prediction time.
    2. Generate forecast using the selected method (persistence or ML).
    3. Generate SELL/WAIT recommendation.
    4. Compare against actual future price (price_after_3_observations) as ground truth.
    5. Record outcome.

Benchmarks against:
    - ALWAYS SELL TODAY strategy
    - ALWAYS WAIT strategy

Metrics:
    - n_sell, n_wait decisions
    - avg_price_after_sell, avg_price_after_wait
    - correct_direction_pct: % of RISING decisions where price actually rose
    - opportunity_gain_from_wait: avg(actual_future - current) when WAIT recommended
    - opportunity_loss_from_wait: loss when WAIT was wrong (future < current)
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUTS_DIR = BASE_DIR / "outputs"

from src.forecast_engine import load_forecast_config, load_metadata, _normalize_crop
from src.price_direction import classify_direction
from src.decision_engine import make_decision
from src.market_regime import classify_regime

CROPS = ["rice", "tomato", "wheat", "cotton"]

TEST_PATHS = {
    "rice": PROCESSED_DIR / "maharashtra_rice_test.csv",
    "tomato": PROCESSED_DIR / "maharashtra_tomato_test.csv",
    "wheat": PROCESSED_DIR / "maharashtra_wheat_test.csv",
    "cotton": PROCESSED_DIR / "maharashtra_cotton_test.csv",
}
FEATURES_PATHS = {
    "rice": PROCESSED_DIR / "maharashtra_rice_features.csv",
    "tomato": PROCESSED_DIR / "maharashtra_tomato_features.csv",
    "wheat": PROCESSED_DIR / "maharashtra_wheat_features.csv",
    "cotton": PROCESSED_DIR / "maharashtra_cotton_features.csv",
}

TARGET_COL = "price_after_3_observations"
PRICE_COL = "Modal Price"
GROUP_COLS = ["Market", "Variety", "Grade"]
DATE_COL = "Price Date"


def _strip_numeric(series: pd.Series) -> pd.Series:
    return (
        series.astype(str).str.replace(",", "", regex=False)
        .str.strip().replace("nan", np.nan).astype(float)
    )


def backtest_crop(crop: str, verbose: bool = True) -> Dict[str, Any]:
    """Run backtest for a single crop on its test set."""
    crop = _normalize_crop(crop)

    test_path = TEST_PATHS[crop]
    if not test_path.exists():
        return {"crop": crop, "error": f"Test file not found: {test_path}"}

    df = pd.read_csv(test_path, low_memory=False)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    df[PRICE_COL] = _strip_numeric(df[PRICE_COL])
    df = df.dropna(subset=[PRICE_COL, TARGET_COL]).copy()

    if df.empty:
        return {"crop": crop, "error": "No valid test rows after dropping NaN."}

    meta = load_metadata(crop)
    validation_mae = meta.get("MAE", meta.get("persistence_baseline_MAE", None))
    config = load_forecast_config()
    method = config.get(crop, {}).get("method", "persistence")

    records = []

    for _, row in df.iterrows():
        current_price = float(row[PRICE_COL])
        actual_future_price = float(row[TARGET_COL])
        ma7 = row.get("price_ma_7", None)

        if current_price <= 0:
            continue

        # Forecast using only info at prediction time
        if method == "persistence":
            predicted_price = current_price
        elif method == "recent_mean":
            predicted_price = float(ma7) if ma7 and not np.isnan(float(ma7)) else current_price
        else:
            predicted_price = current_price  # fallback

        # Collect recent prices for regime (use lag features if available)
        recent_prices = []
        for lag_col in ["price_lag_30", "price_lag_14", "price_lag_7", "price_lag_3",
                         "price_lag_2", "price_lag_1"]:
            if lag_col in row and not pd.isna(row[lag_col]):
                recent_prices.append(float(row[lag_col]))
        recent_prices.append(current_price)

        regime_result = classify_regime(recent_prices)
        regime = regime_result["regime"]

        direction_result = classify_direction(current_price, predicted_price, validation_mae)
        direction = direction_result["direction"]
        expected_change_pct = direction_result["expected_change_pct"]
        stability_threshold_pct = direction_result["stability_threshold_pct"]

        decision_result = make_decision(
            direction=direction,
            expected_change_pct=expected_change_pct,
            stability_threshold_pct=stability_threshold_pct,
            regime=regime,
            forecast_method=method,
        )
        recommendation = decision_result["recommendation"]

        # Ground truth: what actually happened?
        actual_change_pct = ((actual_future_price - current_price) / current_price) * 100
        actual_direction = "RISING" if actual_change_pct > 0.5 else ("FALLING" if actual_change_pct < -0.5 else "STABLE")

        # Was the direction call correct?
        direction_correct = (direction == actual_direction)

        # Opportunity outcome for WAIT decisions
        wait_gain = actual_future_price - current_price  # positive = price rose (WAIT was correct)

        records.append({
            "date": row[DATE_COL],
            "market": row.get("Market", ""),
            "current_price": current_price,
            "predicted_price": predicted_price,
            "actual_future_price": actual_future_price,
            "direction": direction,
            "actual_direction": actual_direction,
            "direction_correct": direction_correct,
            "recommendation": recommendation,
            "actual_change_pct": actual_change_pct,
            "wait_gain": wait_gain,
        })

    if not records:
        return {"crop": crop, "error": "No records produced."}

    df_bt = pd.DataFrame(records)

    # ── Metrics ─────────────────────────────────────────────
    n_sell = (df_bt["recommendation"] == "SELL TODAY").sum()
    n_wait = (df_bt["recommendation"] == "WAIT").sum()
    n_total = len(df_bt)

    dir_accuracy = df_bt["direction_correct"].mean() * 100

    wait_rows = df_bt[df_bt["recommendation"] == "WAIT"]
    sell_rows = df_bt[df_bt["recommendation"] == "SELL TODAY"]

    avg_gain_when_wait = wait_rows["wait_gain"].mean() if len(wait_rows) > 0 else None
    avg_gain_when_sell = sell_rows["wait_gain"].mean() if len(sell_rows) > 0 else None

    # % of WAIT decisions where price actually rose (correct WAIT)
    wait_correct_pct = (
        (wait_rows["actual_direction"] == "RISING").mean() * 100
        if len(wait_rows) > 0 else None
    )

    # Always-sell benchmark
    always_sell_avg_future = df_bt["actual_future_price"].mean()
    always_wait_avg_gain = df_bt["wait_gain"].mean()

    summary = {
        "crop": crop,
        "forecast_method": method,
        "n_test_rows": n_total,
        "n_sell_decisions": int(n_sell),
        "n_wait_decisions": int(n_wait),
        "direction_accuracy_pct": round(dir_accuracy, 2),
        "avg_price_gain_when_wait_recommended": round(avg_gain_when_wait, 2) if avg_gain_when_wait is not None else None,
        "avg_price_gain_when_sell_recommended": round(avg_gain_when_sell, 2) if avg_gain_when_sell is not None else None,
        "wait_correct_pct": round(wait_correct_pct, 2) if wait_correct_pct is not None else None,
        "benchmark_always_sell_avg_future_price": round(always_sell_avg_future, 2),
        "benchmark_always_wait_avg_gain": round(always_wait_avg_gain, 2),
        "validation_mae_used": round(validation_mae, 2) if validation_mae else None,
    }

    if verbose:
        print(f"\n{'='*55}")
        print(f"BACKTEST: {crop.upper()} | Method: {method}")
        print(f"{'='*55}")
        print(f"  Test rows: {n_total}")
        print(f"  SELL decisions: {n_sell} | WAIT decisions: {n_wait}")
        print(f"  Direction accuracy: {dir_accuracy:.1f}%")
        if avg_gain_when_wait is not None:
            print(f"  Avg price gain when WAIT recommended: ₹{avg_gain_when_wait:.2f}")
        if wait_correct_pct is not None:
            print(f"  % WAIT decisions where price actually rose: {wait_correct_pct:.1f}%")
        print(f"  Benchmark (always sell): avg future price ₹{always_sell_avg_future:.2f}")
        print(f"  Benchmark (always wait): avg gain ₹{always_wait_avg_gain:.2f}")

    return {"crop": crop, "summary": summary, "records_df": df_bt}


def backtest_all_crops(verbose: bool = True) -> Dict[str, Dict]:
    """Run backtest for all four crops."""
    all_results = {}
    for crop in CROPS:
        result = backtest_crop(crop, verbose=verbose)
        all_results[crop] = result

    # Save combined summary
    summary_rows = []
    for crop, r in all_results.items():
        if "summary" in r:
            summary_rows.append(r["summary"])

    if summary_rows:
        (OUTPUTS_DIR / "final").mkdir(parents=True, exist_ok=True)
        pd.DataFrame(summary_rows).to_csv(OUTPUTS_DIR / "final" / "decision_backtest_summary.csv", index=False)
        if verbose:
            print(f"\nSaved: outputs/final/decision_backtest_summary.csv")

    return all_results


if __name__ == "__main__":
    results = backtest_all_crops(verbose=True)
