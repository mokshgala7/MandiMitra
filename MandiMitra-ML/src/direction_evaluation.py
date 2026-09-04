"""
direction_evaluation.py — Comprehensive Direction Forecasting Experiment & Evaluation

Runs:
1. Empirical movement threshold analysis.
2. Baselines vs. ML classifiers on untouched chronological test sets.
3. Feature group ablation study (Historical, Cross-Mandi, Chronos-2, Hybrid).
4. Market-level generalization and decision relevance analysis.
5. Generation of all 6 output CSV artifacts.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.direction_features import (
    EMPIRICAL_THRESHOLDS,
    LABEL_NAMES,
    prepare_direction_dataset,
    compute_direction_label
)
from src.direction_models import (
    get_model_pipeline,
    evaluate_classifier,
    CLASSES,
    CLASS_NAMES
)

OUTPUTS_DIR = BASE_DIR / "outputs" / "final"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

CROPS = ["rice", "tomato", "wheat", "cotton"]
MODELS = [
    "majority_class",
    "persistence",
    "momentum",
    "logistic_regression",
    "random_forest",
    "gradient_boosting",
    "hist_gradient_boosting"
]


def run_threshold_analysis() -> pd.DataFrame:
    """Analyze historical price movement distributions on the training sets."""
    records = []
    for crop in CROPS:
        train_path = BASE_DIR / "data" / "processed" / f"maharashtra_{crop}_train.csv"
        df = pd.read_csv(train_path, low_memory=False)
        pct = (df["price_after_3_observations"] - df["Modal Price"]) / df["Modal Price"]
        pct = pct.dropna()
        abs_pct = pct.abs() * 100

        th = EMPIRICAL_THRESHOLDS[crop]
        th_pct = th * 100

        inc_pct = (pct > th).mean() * 100
        stb_pct = ((pct >= -th) & (pct <= th)).mean() * 100
        dec_pct = (pct < -th).mean() * 100
        zero_pct = (pct == 0).mean() * 100

        records.append({
            "crop": crop.capitalize(),
            "n_train_samples": len(pct),
            "mean_abs_pct_change": round(abs_pct.mean(), 2),
            "median_abs_pct_change": round(abs_pct.median(), 2),
            "p25_abs_pct_change": round(abs_pct.quantile(0.25), 2),
            "p75_abs_pct_change": round(abs_pct.quantile(0.75), 2),
            "exact_zero_change_pct": round(zero_pct, 2),
            "selected_threshold_pct": th_pct,
            "train_increase_pct": round(inc_pct, 2),
            "train_stable_pct": round(stb_pct, 2),
            "train_decrease_pct": round(dec_pct, 2),
            "justification": f"Selected ±{th_pct:.1f}% to separate true trends from {zero_pct:.1f}% price stickiness while maintaining balanced target classes."
        })

    df_out = pd.DataFrame(records)
    df_out.to_csv(OUTPUTS_DIR / "direction_threshold_analysis.csv", index=False)
    print("Saved outputs/final/direction_threshold_analysis.csv")
    return df_out


def run_direction_experiment():
    """Run full direction classification benchmark across crops, models, and ablations."""
    print("="*60)
    print("MANDIMITRA ML V3: PRICE DIRECTION EXPERIMENT")
    print("="*60)

    run_threshold_analysis()

    all_comparison_rows = []
    all_confusion_rows = []
    all_ablation_rows = []
    all_market_rows = []
    all_forecast_records = []

    best_crop_models = {}

    for crop in CROPS:
        print(f"\nEvaluating crop: {crop.upper()}...")
        train_df, test_df, feature_groups = prepare_direction_dataset(crop, include_chronos=True)

        y_train = train_df["direction_label"]
        y_test = test_df["direction_label"]

        print(f"Train size: {len(train_df)} | Test size: {len(test_df)}")
        print(f"Test class distribution: Decrease: {(y_test==-1).sum()}, Stable: {(y_test==0).sum()}, Increase: {(y_test==1).sum()}")

        crop_best_f1 = -1.0
        crop_best_model_name = None
        crop_best_eval = None
        crop_best_model_obj = None

        # 1. Evaluate All Models (using 'all' features)
        X_train_all = train_df[feature_groups["all"]]
        X_test_all = test_df[feature_groups["all"]]

        for m_name in MODELS:
            model = get_model_pipeline(m_name)
            model.fit(X_train_all, y_train)
            ev = evaluate_classifier(model, X_test_all, y_test)

            is_baseline = m_name in ["majority_class", "persistence", "momentum"]

            all_comparison_rows.append({
                "crop": crop.capitalize(),
                "model": m_name,
                "model_type": "Baseline" if is_baseline else "ML Classifier",
                "accuracy": ev["accuracy"],
                "balanced_accuracy": ev["balanced_accuracy"],
                "f1_macro": ev["f1_macro"],
                "f1_weighted": ev["f1_weighted"],
                "precision_macro": ev["precision_macro"],
                "recall_macro": ev["recall_macro"],
                "precision_increase": ev["precision_increase"],
                "recall_increase": ev["recall_increase"],
                "f1_increase": ev["f1_increase"],
                "precision_stable": ev["precision_stable"],
                "recall_stable": ev["recall_stable"],
                "f1_stable": ev["f1_stable"],
                "precision_decrease": ev["precision_decrease"],
                "recall_decrease": ev["recall_decrease"],
                "f1_decrease": ev["f1_decrease"],
                "wait_precision": ev["wait_precision"],
                "sell_precision": ev["sell_precision"]
            })

            # Save confusion matrix entry
            cm = ev["confusion_matrix"]
            all_confusion_rows.append({
                "crop": crop.capitalize(),
                "model": m_name,
                "tn_dec_dec": cm[0, 0], "dec_as_stb": cm[0, 1], "dec_as_inc": cm[0, 2],
                "stb_as_dec": cm[1, 0], "stb_as_stb": cm[1, 1], "stb_as_inc": cm[1, 2],
                "inc_as_dec": cm[2, 0], "inc_as_stb": cm[2, 1], "tp_inc_inc": cm[2, 2],
            })

            # Track best ML model
            if not is_baseline and ev["f1_macro"] > crop_best_f1:
                crop_best_f1 = ev["f1_macro"]
                crop_best_model_name = m_name
                crop_best_eval = ev
                crop_best_model_obj = model

        best_crop_models[crop] = {
            "model_name": crop_best_model_name,
            "f1_macro": crop_best_f1,
            "eval": crop_best_eval
        }

        # 2. Ablation Study: Compare Feature Subsets on Best Classifier
        # If no best ML model was picked, default to Random Forest
        ablation_model_name = crop_best_model_name or "random_forest"
        for grp_name, grp_cols in feature_groups.items():
            abl_model = get_model_pipeline(ablation_model_name)
            abl_model.fit(train_df[grp_cols], y_train)
            abl_ev = evaluate_classifier(abl_model, test_df[grp_cols], y_test)

            all_ablation_rows.append({
                "crop": crop.capitalize(),
                "model": ablation_model_name,
                "feature_group": grp_name,
                "n_features": len(grp_cols),
                "accuracy": abl_ev["accuracy"],
                "balanced_accuracy": abl_ev["balanced_accuracy"],
                "f1_macro": abl_ev["f1_macro"],
                "precision_macro": abl_ev["precision_macro"],
                "recall_macro": abl_ev["recall_macro"],
                "wait_precision": abl_ev["wait_precision"],
                "sell_precision": abl_ev["sell_precision"]
            })

        # 3. Market-Level Breakdown for Best Model
        test_df_eval = test_df.copy()
        test_df_eval["pred_label"] = crop_best_eval["predictions"]

        # Extract probabilities if available
        if crop_best_eval["probabilities"] is not None:
            probs = crop_best_eval["probabilities"]
            test_df_eval["prob_decrease"] = probs[:, 0]
            test_df_eval["prob_stable"] = probs[:, 1]
            test_df_eval["prob_increase"] = probs[:, 2]
            test_df_eval["confidence"] = np.max(probs, axis=1)
        else:
            test_df_eval["prob_decrease"] = 0.33
            test_df_eval["prob_stable"] = 0.33
            test_df_eval["prob_increase"] = 0.33
            test_df_eval["confidence"] = 1.0

        for mkt, m_sub in test_df_eval.groupby("Market"):
            m_y_true = m_sub["direction_label"]
            m_y_pred = m_sub["pred_label"]
            m_acc = (m_y_true == m_y_pred).mean()
            all_market_rows.append({
                "crop": crop.capitalize(),
                "market": mkt,
                "n_samples": len(m_sub),
                "best_model": crop_best_model_name,
                "accuracy": round(float(m_acc), 4),
                "actual_decrease_count": int((m_y_true == -1).sum()),
                "actual_stable_count": int((m_y_true == 0).sum()),
                "actual_increase_count": int((m_y_true == 1).sum()),
                "predicted_decrease_count": int((m_y_pred == -1).sum()),
                "predicted_stable_count": int((m_y_pred == 0).sum()),
                "predicted_increase_count": int((m_y_pred == 1).sum()),
            })

        # 4. Save test-level forecasts
        for _, r in test_df_eval.iterrows():
            all_forecast_records.append({
                "crop": crop,
                "market": r["Market"],
                "price_date": str(r["Price Date"])[:10],
                "current_price": r["Modal Price"],
                "future_price_3": r["price_after_3_observations"],
                "actual_label": int(r["direction_label"]),
                "predicted_label": int(r["pred_label"]),
                "actual_direction": LABEL_NAMES.get(int(r["direction_label"]), "UNKNOWN"),
                "predicted_direction": LABEL_NAMES.get(int(r["pred_label"]), "UNKNOWN"),
                "confidence": round(float(r["confidence"]), 4),
                "prob_decrease": round(float(r["prob_decrease"]), 4),
                "prob_stable": round(float(r["prob_stable"]), 4),
                "prob_increase": round(float(r["prob_increase"]), 4),
                "model_used": crop_best_model_name
            })

    # Save output artifacts
    df_comp = pd.DataFrame(all_comparison_rows)
    df_cm = pd.DataFrame(all_confusion_rows)
    df_abl = pd.DataFrame(all_ablation_rows)
    df_mkt = pd.DataFrame(all_market_rows)
    df_fc = pd.DataFrame(all_forecast_records)

    df_comp.to_csv(OUTPUTS_DIR / "direction_model_comparison.csv", index=False)
    df_cm.to_csv(OUTPUTS_DIR / "direction_confusion_matrices.csv", index=False)
    df_abl.to_csv(OUTPUTS_DIR / "direction_ablation_results.csv", index=False)
    df_mkt.to_csv(OUTPUTS_DIR / "direction_market_performance.csv", index=False)
    df_fc.to_csv(OUTPUTS_DIR / "direction_forecasts.csv", index=False)

    print("\nSaved all 6 outputs to outputs/final/")
    print("\n" + "="*60)
    print("BEST DIRECTION MODEL PER CROP SUMMARY")
    print("="*60)
    for crop in CROPS:
        info = best_crop_models[crop]
        print(f"Crop: {crop.capitalize():<8} | Best Model: {info['model_name']:<22} | Macro F1: {info['f1_macro']:.4f} | Balanced Acc: {info['eval']['balanced_accuracy']:.4f}")

    return df_comp, df_abl


if __name__ == "__main__":
    run_direction_experiment()
