"""
Multi-Crop Model Training and Evaluation Pipeline for MandiMitra.
Trains Linear Regression, Random Forest, and Gradient Boosting independently
for Tomato, Wheat, and Cotton.

Rice pipeline (src/train.py, models/mandimitra_rice_price_model.joblib) is NOT touched.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    r2_score,
    root_mean_squared_error,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"

CROPS = ["Tomato", "Wheat", "Cotton"]

TRAIN_PATHS = {
    "Tomato": PROCESSED_DIR / "maharashtra_tomato_train.csv",
    "Wheat": PROCESSED_DIR / "maharashtra_wheat_train.csv",
    "Cotton": PROCESSED_DIR / "maharashtra_cotton_train.csv",
}
TEST_PATHS = {
    "Tomato": PROCESSED_DIR / "maharashtra_tomato_test.csv",
    "Wheat": PROCESSED_DIR / "maharashtra_wheat_test.csv",
    "Cotton": PROCESSED_DIR / "maharashtra_cotton_test.csv",
}
MODEL_SAVE_PATHS = {
    "Tomato": MODELS_DIR / "mandimitra_tomato_price_model.joblib",
    "Wheat": MODELS_DIR / "mandimitra_wheat_price_model.joblib",
    "Cotton": MODELS_DIR / "mandimitra_cotton_price_model.joblib",
}
METADATA_SAVE_PATHS = {
    "Tomato": MODELS_DIR / "tomato_model_metadata.json",
    "Wheat": MODELS_DIR / "wheat_model_metadata.json",
    "Cotton": MODELS_DIR / "cotton_model_metadata.json",
}

OBSERVATION_THRESHOLDS = {
    "Tomato": 500,
    "Wheat": 500,
    "Cotton": 300,  # Adaptive — seasonal crop; no group reaches 500
}
COTTON_DATA_LIMITATION = (
    "No Market+Variety+Grade group reached 500 observations; "
    "adaptive threshold of 300 was used. Cotton is a seasonal crop "
    "with restricted Oct–Feb harvest reporting. Model performance "
    "and generalization should be interpreted cautiously."
)

FEATURE_COLUMNS = [
    "Min Price", "Max Price", "Modal Price",
    "price_lag_1", "price_lag_2", "price_lag_3",
    "price_lag_7", "price_lag_14", "price_lag_30",
    "price_ma_3", "price_ma_7", "price_ma_14", "price_ma_30",
    "price_std_7", "price_std_14", "price_std_30",
    "price_change_1", "price_change_1_pct",
    "price_change_3", "price_change_3_pct",
    "price_change_7", "price_change_7_pct",
    "price_change_14", "price_change_14_pct",
    "price_range", "price_range_pct",
    "year", "month", "day", "day_of_week", "day_of_year",
    "week_of_year", "is_weekend",
    "month_sin", "month_cos", "day_of_year_sin", "day_of_year_cos",
    "Market", "Variety", "Grade",
]

TARGET_COLUMN = "price_after_3_observations"
CATEGORICAL_COLUMNS = ["Market", "Variety", "Grade"]
NUMERICAL_COLUMNS = [c for c in FEATURE_COLUMNS if c not in CATEGORICAL_COLUMNS]

# Forbidden columns — must NEVER appear as input features
FORBIDDEN_COLUMNS = [
    "price_next_observation",
    "price_after_3_observations",
    "price_after_7_observations",
    "future_price_change_3",
    "future_price_change_7",
    "target_date_3",
    "target_date_7",
    "target_date",
    "target_realization_date",
]


# ──────────────────────────────────────────────────────────────
# Data Loading
# ──────────────────────────────────────────────────────────────

def _strip_numeric(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
        .replace("nan", np.nan)
        .astype(float)
    )


def load_and_clean_data(
    crop: str,
    features: List[str] = None,
    target: str = TARGET_COLUMN,
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, Dict[str, int], pd.DataFrame, pd.DataFrame]:
    """
    Load train/test CSVs for a crop, drop rows with missing feature values
    or missing target, return cleaned splits.
    Source CSVs are never modified.
    """
    if features is None:
        features = FEATURE_COLUMNS

    train_path = TRAIN_PATHS[crop]
    test_path = TEST_PATHS[crop]

    df_train = pd.read_csv(train_path, low_memory=False)
    df_test = pd.read_csv(test_path, low_memory=False)

    # Parse numeric prices (may have comma-thousands)
    for col in ["Min Price", "Max Price", "Modal Price"]:
        if col in df_train.columns:
            df_train[col] = _strip_numeric(df_train[col])
            df_test[col] = _strip_numeric(df_test[col])

    stats = {
        "train_rows_before": len(df_train),
        "test_rows_before": len(df_test),
    }

    # Leakage guard: ensure no forbidden columns in feature list
    for fc in FORBIDDEN_COLUMNS:
        if fc in features:
            raise ValueError(f"LEAKAGE ALERT: forbidden column '{fc}' found in feature list for {crop}.")

    # Drop rows missing any required feature or the target
    required = [f for f in features if f in df_train.columns] + [target]
    train_clean = df_train.dropna(subset=required).copy()
    test_clean = df_test.dropna(subset=[f for f in features if f in df_test.columns] + [target]).copy()

    stats["train_rows_after"] = len(train_clean)
    stats["test_rows_after"] = len(test_clean)
    stats["train_rows_removed"] = stats["train_rows_before"] - stats["train_rows_after"]
    stats["test_rows_removed"] = stats["test_rows_before"] - stats["test_rows_after"]

    # Ensure features exist in data
    avail_features = [f for f in features if f in train_clean.columns]
    X_train = train_clean[avail_features].copy()
    y_train = train_clean[target].copy()
    X_test = test_clean[avail_features].copy()
    y_test = test_clean[target].copy()

    return X_train, y_train, X_test, y_test, stats, train_clean, test_clean


# ──────────────────────────────────────────────────────────────
# Model Definitions
# ──────────────────────────────────────────────────────────────

def _build_preprocessor(numerical_cols: List[str], categorical_cols: List[str], for_linear: bool = False):
    """Build ColumnTransformer with OHE for categoricals, optional StandardScaler for numericals."""
    numeric_transformer = StandardScaler() if for_linear else "passthrough"
    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numerical_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_cols),
        ],
        remainder="drop",
    )


def build_candidate_models(
    numerical_cols: List[str],
    categorical_cols: List[str],
    random_state: int = 42,
) -> Dict[str, Pipeline]:
    """
    Construct sklearn Pipeline objects for all candidate models.
    XGBoost is attempted but gracefully skipped if unavailable.
    """
    models = {}

    # Model 1: Linear Regression (with StandardScaler)
    models["Linear Regression"] = Pipeline([
        ("prep", _build_preprocessor(numerical_cols, categorical_cols, for_linear=True)),
        ("reg", LinearRegression()),
    ])

    # Model 2: Random Forest
    models["Random Forest"] = Pipeline([
        ("prep", _build_preprocessor(numerical_cols, categorical_cols, for_linear=False)),
        ("reg", RandomForestRegressor(
            n_estimators=300,
            max_features="sqrt",
            random_state=random_state,
            n_jobs=-1,
        )),
    ])

    # Model 3: Gradient Boosting
    models["Gradient Boosting"] = Pipeline([
        ("prep", _build_preprocessor(numerical_cols, categorical_cols, for_linear=False)),
        ("reg", GradientBoostingRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=3,
            random_state=random_state,
        )),
    ])

    # Model 4: XGBoost (conditional)
    try:
        from xgboost import XGBRegressor
        models["XGBoost"] = Pipeline([
            ("prep", _build_preprocessor(numerical_cols, categorical_cols, for_linear=False)),
            ("reg", XGBRegressor(
                n_estimators=300,
                learning_rate=0.05,
                max_depth=3,
                random_state=random_state,
                n_jobs=-1,
                verbosity=0,
            )),
        ])
        print("  XGBoost: available and included.")
    except Exception as e:
        print(f"  XGBoost: SKIPPED — {type(e).__name__}: {e}")

    return models


# ──────────────────────────────────────────────────────────────
# Metrics
# ──────────────────────────────────────────────────────────────

def _compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(root_mean_squared_error(y_true, y_pred))
    mape = float(mean_absolute_percentage_error(y_true, y_pred)) * 100
    r2 = float(r2_score(y_true, y_pred))
    return {"MAE": round(mae, 4), "RMSE": round(rmse, 4), "MAPE": round(mape, 4), "R2": round(r2, 4)}


def compute_baselines(
    test_clean: pd.DataFrame,
    y_test: pd.Series,
    target: str = TARGET_COLUMN,
) -> Dict[str, Dict[str, float]]:
    """Compute Persistence and Recent-Mean (MA-7) baselines."""
    baselines = {}

    # Persistence: predict current Modal Price
    if "Modal Price" in test_clean.columns:
        modal = test_clean.loc[y_test.index, "Modal Price"]
        valid = y_test.notna() & modal.notna()
        if valid.sum() > 0:
            baselines["Persistence"] = _compute_metrics(y_test[valid].values, modal[valid].values)

    # Recent Mean: predict price_ma_7
    if "price_ma_7" in test_clean.columns:
        ma7 = test_clean.loc[y_test.index, "price_ma_7"]
        valid = y_test.notna() & ma7.notna()
        if valid.sum() > 0:
            baselines["Recent Mean (MA-7)"] = _compute_metrics(y_test[valid].values, ma7[valid].values)

    return baselines


# ──────────────────────────────────────────────────────────────
# Training & Evaluation
# ──────────────────────────────────────────────────────────────

def train_and_evaluate(
    crop: str,
    models: Dict[str, Pipeline],
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    baselines: Dict[str, Dict[str, float]],
    verbose: bool = True,
) -> Tuple[Dict[str, Pipeline], Dict[str, np.ndarray], pd.DataFrame]:
    """Fit all models on train, evaluate on test, return results DataFrame."""
    results = []
    predictions = {}
    persistence_mae = baselines.get("Persistence", {}).get("MAE", np.nan)

    for name, pipeline in models.items():
        if verbose:
            print(f"  Fitting {name}...")
        pipeline.fit(X_train, y_train)
        preds = pipeline.predict(X_test)
        predictions[name] = preds
        metrics = _compute_metrics(y_test.values, preds)
        improvement = (
            round(((persistence_mae - metrics["MAE"]) / persistence_mae) * 100, 4)
            if not np.isnan(persistence_mae) and persistence_mae > 0
            else np.nan
        )
        results.append({
            "Model": name,
            **metrics,
            "Persistence_MAE": persistence_mae,
            "Improvement_vs_Persistence_MAE_pct": improvement,
        })
        if verbose:
            print(f"    MAE=₹{metrics['MAE']:.2f} | RMSE=₹{metrics['RMSE']:.2f} | "
                  f"MAPE={metrics['MAPE']:.2f}% | R²={metrics['R2']:.4f}")

    results_df = pd.DataFrame(results).sort_values("MAE").reset_index(drop=True)
    return models, predictions, results_df


# ──────────────────────────────────────────────────────────────
# Residual Analysis
# ──────────────────────────────────────────────────────────────

def analyze_residuals(
    test_clean: pd.DataFrame,
    y_test: pd.Series,
    y_pred: np.ndarray,
) -> Tuple[Dict, pd.DataFrame, pd.DataFrame]:
    """Compute residual stats overall and by Market and Month."""
    residuals = y_test.values - y_pred
    overall = {
        "mean_error": round(float(residuals.mean()), 4),
        "median_error": round(float(np.median(residuals)), 4),
        "MAE": round(float(np.abs(residuals).mean()), 4),
        "RMSE": round(float(np.sqrt((residuals ** 2).mean())), 4),
        "MAPE": round(float(mean_absolute_percentage_error(y_test.values, y_pred)) * 100, 4),
        "max_abs_error": round(float(np.abs(residuals).max()), 4),
    }

    test_aligned = test_clean.loc[y_test.index].copy()
    test_aligned["_residual"] = residuals
    test_aligned["_abs_residual"] = np.abs(residuals)
    test_aligned["_pred"] = y_pred
    test_aligned["_actual"] = y_test.values

    # By Market
    market_rows = []
    for mkt, grp in test_aligned.groupby("Market"):
        market_rows.append({
            "Market": mkt,
            "N_obs": len(grp),
            "Mean_Error": round(grp["_residual"].mean(), 4),
            "Median_Error": round(grp["_residual"].median(), 4),
            "MAE": round(grp["_abs_residual"].mean(), 4),
            "RMSE": round(np.sqrt((grp["_residual"] ** 2).mean()), 4),
            "MAPE_%": round(mean_absolute_percentage_error(grp["_actual"], grp["_pred"]) * 100, 4),
            "Max_Abs_Error": round(grp["_abs_residual"].max(), 4),
        })
    market_df = pd.DataFrame(market_rows).sort_values("MAE").reset_index(drop=True)

    # By Month
    test_aligned["_ym"] = pd.to_datetime(test_clean.loc[y_test.index, "Price Date"]).dt.to_period("M")
    month_rows = []
    for ym, grp in test_aligned.groupby("_ym"):
        month_rows.append({
            "Month": str(ym),
            "N_obs": len(grp),
            "Mean_Error": round(grp["_residual"].mean(), 4),
            "MAE": round(grp["_abs_residual"].mean(), 4),
            "RMSE": round(np.sqrt((grp["_residual"] ** 2).mean()), 4),
            "MAPE_%": round(mean_absolute_percentage_error(grp["_actual"], grp["_pred"]) * 100, 4),
        })
    month_df = pd.DataFrame(month_rows).sort_values("Month").reset_index(drop=True)

    return overall, market_df, month_df


# ──────────────────────────────────────────────────────────────
# Feature Importance
# ──────────────────────────────────────────────────────────────

def extract_feature_importances(
    pipeline: Pipeline,
    numerical_cols: List[str],
    categorical_cols: List[str],
) -> Optional[pd.DataFrame]:
    """Extract and map feature importances for tree-based models."""
    estimator = pipeline.named_steps["reg"]
    if not hasattr(estimator, "feature_importances_"):
        return None

    prep = pipeline.named_steps["prep"]
    # Get feature names from preprocessor
    try:
        ohe = prep.named_transformers_["cat"]
        cat_feature_names = list(ohe.get_feature_names_out(categorical_cols))
    except Exception:
        cat_feature_names = []

    num_feature_names = numerical_cols
    all_feature_names = num_feature_names + cat_feature_names

    importances = estimator.feature_importances_
    if len(importances) != len(all_feature_names):
        # Fallback: try sklearn get_feature_names_out
        try:
            all_feature_names = list(prep.get_feature_names_out())
        except Exception:
            all_feature_names = [f"feature_{i}" for i in range(len(importances))]

    fi_df = pd.DataFrame({
        "feature": all_feature_names[:len(importances)],
        "importance": importances,
    }).sort_values("importance", ascending=False).reset_index(drop=True)
    return fi_df


# ──────────────────────────────────────────────────────────────
# Full Crop Training Pipeline
# ──────────────────────────────────────────────────────────────

def run_crop_pipeline(
    crop: str,
    verbose: bool = True,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Run the complete training pipeline for one crop:
    load → clean → baselines → train → evaluate → residuals → importance → save.
    Returns a dict of all results.
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"CROP: {crop.upper()}")
        print(f"{'='*60}")
        if crop == "Cotton":
            print(f"  COTTON DATA LIMITATION: {COTTON_DATA_LIMITATION}")

    # Load and clean data
    X_train, y_train, X_test, y_test, stats, train_clean, test_clean = load_and_clean_data(crop)

    if verbose:
        print(f"  Train: {stats['train_rows_before']:,} → {stats['train_rows_after']:,} rows "
              f"({stats['train_rows_removed']} removed for NaN features/target)")
        print(f"  Test : {stats['test_rows_before']:,} → {stats['test_rows_after']:,} rows "
              f"({stats['test_rows_removed']} removed for NaN features/target)")

    # Leakage validation
    for col in FORBIDDEN_COLUMNS:
        assert col not in X_train.columns, f"LEAKAGE: {col} in X_train for {crop}"
    assert X_train.isna().sum().sum() == 0, f"NaN in X_train for {crop}"
    assert X_test.isna().sum().sum() == 0, f"NaN in X_test for {crop}"

    # Actual feature columns present (may vary slightly if some are absent)
    actual_num = [c for c in NUMERICAL_COLUMNS if c in X_train.columns]
    actual_cat = [c for c in CATEGORICAL_COLUMNS if c in X_train.columns]

    # Compute baselines on test data
    baselines = compute_baselines(test_clean, y_test)
    if verbose:
        for bname, bmetrics in baselines.items():
            print(f"  Baseline [{bname}]: MAE=₹{bmetrics['MAE']:.2f} | RMSE=₹{bmetrics['RMSE']:.2f} | MAPE={bmetrics['MAPE']:.2f}%")

    # Build candidate models
    models_dict = build_candidate_models(actual_num, actual_cat, random_state=random_state)

    # Train & evaluate
    trained_models, predictions, results_df = train_and_evaluate(
        crop, models_dict, X_train, y_train, X_test, y_test, baselines, verbose=verbose
    )

    # Best ML model by MAE
    best_model_name = results_df.iloc[0]["Model"]
    best_pipeline = trained_models[best_model_name]
    best_preds = predictions[best_model_name]
    best_metrics = results_df.iloc[0].to_dict()

    if verbose:
        persistence_mae = baselines.get("Persistence", {}).get("MAE", np.nan)
        beats = "YES" if best_metrics["MAE"] < persistence_mae else "NO"
        print(f"\n  Best ML model: {best_model_name}")
        print(f"    MAE=₹{best_metrics['MAE']:.2f} | Persistence MAE=₹{persistence_mae:.2f} | Beats Persistence: {beats}")

    # Residual analysis
    overall_err, market_err_df, month_err_df = analyze_residuals(test_clean, y_test, best_preds)

    # Feature importance
    fi_df = extract_feature_importances(best_pipeline, actual_num, actual_cat)

    # ── Save model outputs ──────────────────────────────────────
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "model_comparison").mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "model_error").mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "feature_importance").mkdir(parents=True, exist_ok=True)

    # Model artifacts
    joblib.dump(best_pipeline, MODEL_SAVE_PATHS[crop])

    # Model comparison CSVs
    results_df.to_csv(OUTPUTS_DIR / "model_comparison" / f"{crop.lower()}_model_comparison.csv", index=False)

    # Residual CSVs
    market_err_df.to_csv(OUTPUTS_DIR / "model_error" / f"{crop.lower()}_error_by_market.csv", index=False)
    month_err_df.to_csv(OUTPUTS_DIR / "model_error" / f"{crop.lower()}_error_by_month.csv", index=False)

    # Feature importance CSV
    if fi_df is not None:
        fi_df.to_csv(OUTPUTS_DIR / "feature_importance" / f"{crop.lower()}_feature_importance.csv", index=False)

    # Metadata JSON
    persistence_baseline = baselines.get("Persistence", {})
    metadata = {
        "crop": crop,
        "model_name": best_model_name,
        "target": TARGET_COLUMN,
        "training_start_date": str(train_clean["Price Date"].min())[:10],
        "training_end_date": str(train_clean["Price Date"].max())[:10],
        "test_start_date": str(test_clean["Price Date"].min())[:10],
        "test_end_date": str(test_clean["Price Date"].max())[:10],
        "train_rows": len(X_train),
        "test_rows_used_for_evaluation": len(X_test),
        "MAE": best_metrics["MAE"],
        "RMSE": best_metrics["RMSE"],
        "MAPE": best_metrics["MAPE"],
        "R2": best_metrics["R2"],
        "persistence_baseline_MAE": persistence_baseline.get("MAE", None),
        "persistence_baseline_RMSE": persistence_baseline.get("RMSE", None),
        "persistence_baseline_MAPE": persistence_baseline.get("MAPE", None),
        "improvement_vs_persistence_pct": best_metrics.get("Improvement_vs_Persistence_MAE_pct", None),
        "feature_list": [c for c in FEATURE_COLUMNS if c in X_train.columns],
        "markets": sorted(train_clean["Market"].dropna().unique().tolist()),
        "varieties": sorted(train_clean["Variety"].dropna().unique().tolist()),
        "grades": sorted(train_clean["Grade"].dropna().unique().tolist()),
        "observation_threshold": OBSERVATION_THRESHOLDS[crop],
        "random_state": random_state,
    }
    if crop == "Cotton":
        metadata["data_limitation"] = COTTON_DATA_LIMITATION

    with open(METADATA_SAVE_PATHS[crop], "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    if verbose:
        print(f"  Saved model: {MODEL_SAVE_PATHS[crop].relative_to(BASE_DIR)}")
        print(f"  Saved metadata: {METADATA_SAVE_PATHS[crop].relative_to(BASE_DIR)}")

    # Reload validation (Part N)
    reloaded = joblib.load(MODEL_SAVE_PATHS[crop])
    reloaded_preds = reloaded.predict(X_test)
    assert np.allclose(best_preds, reloaded_preds), f"RELOAD MISMATCH for {crop}!"
    if verbose:
        print(f"  [PASSED] Model reload validation: predictions are bit-for-bit identical.")

    return {
        "crop": crop,
        "X_train": X_train,
        "y_train": y_train,
        "X_test": X_test,
        "y_test": y_test,
        "train_clean": train_clean,
        "test_clean": test_clean,
        "stats": stats,
        "baselines": baselines,
        "models": trained_models,
        "predictions": predictions,
        "results_df": results_df,
        "best_model_name": best_model_name,
        "best_pipeline": best_pipeline,
        "best_preds": best_preds,
        "best_metrics": best_metrics,
        "overall_err": overall_err,
        "market_err_df": market_err_df,
        "month_err_df": month_err_df,
        "fi_df": fi_df,
        "metadata": metadata,
    }


def run_all_crops(verbose: bool = True) -> Dict[str, Dict]:
    """Run complete training pipeline for Tomato, Wheat, and Cotton."""
    all_results = {}
    combined_rows = []

    for crop in CROPS:
        result = run_crop_pipeline(crop, verbose=verbose)
        all_results[crop] = result

        persistence_mae = result["baselines"].get("Persistence", {}).get("MAE", np.nan)
        combined_rows.append({
            "crop": crop,
            "model": result["best_model_name"],
            "MAE": result["best_metrics"]["MAE"],
            "RMSE": result["best_metrics"]["RMSE"],
            "MAPE": result["best_metrics"]["MAPE"],
            "R2": result["best_metrics"]["R2"],
            "persistence_MAE": persistence_mae,
            "improvement_vs_persistence_MAE_pct": result["best_metrics"].get("Improvement_vs_Persistence_MAE_pct", np.nan),
        })

    # Save combined comparison
    combined_df = pd.DataFrame(combined_rows)
    combined_df.to_csv(OUTPUTS_DIR / "multi_crop_model_comparison.csv", index=False)
    if verbose:
        print(f"\nSaved: outputs/multi_crop_model_comparison.csv")

    return all_results


if __name__ == "__main__":
    results = run_all_crops(verbose=True)
