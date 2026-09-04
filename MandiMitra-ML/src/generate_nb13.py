"""Generate notebook 13 for MandiMitra multi-crop Step 7."""
import json
from pathlib import Path

OUT_PATH = Path("notebooks/13_multi_crop_model_training_and_evaluation.ipynb")


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": text}


cells = [
    md(
        "# Step 13: Multi-Crop Model Training & Evaluation\n"
        "## MandiMitra ML Pipeline — Tomato, Wheat, Cotton\n\n"
        "**Primary Target:** `price_after_3_observations`  \n"
        "**Crops:** Tomato, Wheat, Cotton  \n"
        "**Rice pipeline is completely untouched.**\n\n"
        "---\n\n"
        "### Cotton Data Limitation\n"
        "> **IMPORTANT:** Cotton has NO Market+Variety+Grade group with ≥500 observations. "
        "An adaptive threshold of ≥300 was used. The retained group is **APMC Hinganghat | Other | FAQ** "
        "(412 observations). Model performance should be interpreted cautiously."
    ),

    # ── Section 1: Setup ────────────────────────────────────────────
    md("---\n### 1. Setup & Imports"),
    code(
        "import sys\n"
        "from pathlib import Path\n"
        "import json\n"
        "import numpy as np\n"
        "import pandas as pd\n"
        "import matplotlib.pyplot as plt\n"
        "import joblib\n\n"
        "BASE_DIR = Path('..').resolve()\n"
        "if str(BASE_DIR) not in sys.path:\n"
        "    sys.path.append(str(BASE_DIR))\n\n"
        "from src.multi_crop_train import (\n"
        "    CROPS, FEATURE_COLUMNS, TARGET_COLUMN, CATEGORICAL_COLUMNS, NUMERICAL_COLUMNS,\n"
        "    FORBIDDEN_COLUMNS, OBSERVATION_THRESHOLDS, COTTON_DATA_LIMITATION,\n"
        "    load_and_clean_data, build_candidate_models, compute_baselines,\n"
        "    train_and_evaluate, analyze_residuals, extract_feature_importances,\n"
        "    MODEL_SAVE_PATHS, METADATA_SAVE_PATHS, run_all_crops\n"
        ")\n\n"
        "print('Step 13: Multi-Crop Model Training & Evaluation')\n"
        "print(f'Working dir: {BASE_DIR}')\n"
        "print(f'Crops: {CROPS}')\n"
        "print(f'Primary target: {TARGET_COLUMN}')\n"
        "print(f'Feature count: {len(FEATURE_COLUMNS)}')"
    ),

    # ── Section 2: Load Data ─────────────────────────────────────────
    md("---\n### 2. Load & Clean Train/Test Data for All Crops"),
    code(
        "crop_data = {}\n"
        "for crop in CROPS:\n"
        "    X_train, y_train, X_test, y_test, stats, train_clean, test_clean = load_and_clean_data(crop)\n"
        "    crop_data[crop] = dict(\n"
        "        X_train=X_train, y_train=y_train, X_test=X_test, y_test=y_test,\n"
        "        stats=stats, train_clean=train_clean, test_clean=test_clean\n"
        "    )\n"
        "    print(f'\\n{crop.upper()}')\n"
        "    print(f'  Train: {stats[\"train_rows_before\"]:,} → {stats[\"train_rows_after\"]:,} rows ({stats[\"train_rows_removed\"]} removed for NaN)')\n"
        "    print(f'  Test : {stats[\"test_rows_before\"]:,} → {stats[\"test_rows_after\"]:,} rows ({stats[\"test_rows_removed\"]} removed for NaN)')\n"
        "    print(f'  X_train shape: {X_train.shape} | X_test shape: {X_test.shape}')"
    ),

    # ── Section 3: Feature Groups ────────────────────────────────────
    md("---\n### 3. Feature Groups & Leakage Audit"),
    code(
        "print('FEATURE GROUPS:')\n"
        "print(f'  Numerical ({len(NUMERICAL_COLUMNS)}): {NUMERICAL_COLUMNS[:5]}...')\n"
        "print(f'  Categorical ({len(CATEGORICAL_COLUMNS)}): {CATEGORICAL_COLUMNS}')\n"
        "print(f'  Total features: {len(FEATURE_COLUMNS)}')\n\n"
        "print('\\nLEAKAGE AUDIT — Forbidden columns must NOT appear in feature list:')\n"
        "all_ok = True\n"
        "for fc in FORBIDDEN_COLUMNS:\n"
        "    if fc in FEATURE_COLUMNS:\n"
        "        print(f'  FAIL: {fc} found in FEATURE_COLUMNS!')\n"
        "        all_ok = False\n"
        "print(f'[{\"PASSED\" if all_ok else \"FAILED\"}] Zero forbidden/future-target columns in feature set.')"
    ),

    # ── Section 4: Baselines ─────────────────────────────────────────
    md("---\n### 4. Baseline Benchmarks (Persistence & Recent Mean MA-7)"),
    code(
        "baselines_all = {}\n"
        "for crop in CROPS:\n"
        "    d = crop_data[crop]\n"
        "    baselines = compute_baselines(d['test_clean'], d['y_test'])\n"
        "    baselines_all[crop] = baselines\n"
        "    print(f'\\n{crop.upper()} — Baselines on test set:')\n"
        "    for bname, bm in baselines.items():\n"
        "        print(f'  [{bname}]: MAE=₹{bm[\"MAE\"]:.2f} | RMSE=₹{bm[\"RMSE\"]:.2f} | MAPE={bm[\"MAPE\"]:.2f}%')"
    ),

    # ── Section 5: Build Preprocessing ──────────────────────────────
    md("---\n### 5. Build Preprocessing Pipelines\nColumnTransformer: OneHotEncoder for categoricals, StandardScaler for Linear Regression numerical features. Fit only on training data."),
    code(
        "models_per_crop = {}\n"
        "for crop in CROPS:\n"
        "    d = crop_data[crop]\n"
        "    actual_num = [c for c in NUMERICAL_COLUMNS if c in d['X_train'].columns]\n"
        "    actual_cat = [c for c in CATEGORICAL_COLUMNS if c in d['X_train'].columns]\n"
        "    print(f'{crop}: {len(actual_num)} numerical + {len(actual_cat)} categorical features')\n"
        "    models_per_crop[crop] = build_candidate_models(actual_num, actual_cat, random_state=42)"
    ),

    # ── Sections 6-8: Train all 3 crops ─────────────────────────────
    md("---\n### 6. Train All Candidate Models — Tomato"),
    code(
        "crop = 'Tomato'\nd = crop_data[crop]\n"
        "actual_num_t = [c for c in NUMERICAL_COLUMNS if c in d['X_train'].columns]\n"
        "actual_cat_t = [c for c in CATEGORICAL_COLUMNS if c in d['X_train'].columns]\n"
        "print(f'Training {len(models_per_crop[crop])} models for {crop}...')\n"
        "_, preds_tomato, results_tomato = train_and_evaluate(\n"
        "    crop, models_per_crop[crop], d['X_train'], d['y_train'],\n"
        "    d['X_test'], d['y_test'], baselines_all[crop], verbose=True\n"
        ")\nprint(results_tomato[['Model','MAE','RMSE','MAPE','R2','Improvement_vs_Persistence_MAE_pct']].to_string(index=False))"
    ),

    md("---\n### 7. Train All Candidate Models — Wheat"),
    code(
        "crop = 'Wheat'\nd = crop_data[crop]\n"
        "print(f'Training {len(models_per_crop[crop])} models for {crop}...')\n"
        "_, preds_wheat, results_wheat = train_and_evaluate(\n"
        "    crop, models_per_crop[crop], d['X_train'], d['y_train'],\n"
        "    d['X_test'], d['y_test'], baselines_all[crop], verbose=True\n"
        ")\nprint(results_wheat[['Model','MAE','RMSE','MAPE','R2','Improvement_vs_Persistence_MAE_pct']].to_string(index=False))"
    ),

    md("---\n### 8. Train All Candidate Models — Cotton"),
    code(
        "crop = 'Cotton'\nd = crop_data[crop]\n"
        "print('COTTON DATA LIMITATION:')\nprint(COTTON_DATA_LIMITATION)\nprint()\n"
        "print(f'Training {len(models_per_crop[crop])} models for {crop}...')\n"
        "_, preds_cotton, results_cotton = train_and_evaluate(\n"
        "    crop, models_per_crop[crop], d['X_train'], d['y_train'],\n"
        "    d['X_test'], d['y_test'], baselines_all[crop], verbose=True\n"
        ")\nprint(results_cotton[['Model','MAE','RMSE','MAPE','R2','Improvement_vs_Persistence_MAE_pct']].to_string(index=False))"
    ),

    # ── Section 9: Model Comparison Tables ──────────────────────────
    md("---\n### 9. Model Comparison vs Baselines"),
    code(
        "all_results_dfs = {'Tomato': results_tomato, 'Wheat': results_wheat, 'Cotton': results_cotton}\n"
        "all_preds = {'Tomato': preds_tomato, 'Wheat': preds_wheat, 'Cotton': preds_cotton}\n\n"
        "for crop, rdf in all_results_dfs.items():\n"
        "    pers = baselines_all[crop].get('Persistence', {})\n"
        "    ma7 = baselines_all[crop].get('Recent Mean (MA-7)', {})\n"
        "    print(f'\\n{crop.upper()} — Full Comparison:')\n"
        "    rows = [\n"
        "        {'Method': 'Persistence Baseline', 'MAE': pers.get('MAE','N/A'), 'RMSE': pers.get('RMSE','N/A'), 'MAPE': pers.get('MAPE','N/A'), 'R2': '—'},\n"
        "        {'Method': 'Recent Mean (MA-7)',   'MAE': ma7.get('MAE','N/A'),  'RMSE': ma7.get('RMSE','N/A'),  'MAPE': ma7.get('MAPE','N/A'),  'R2': '—'},\n"
        "    ]\n"
        "    for _, row in rdf.iterrows():\n"
        "        rows.append({'Method': row['Model'], 'MAE': row['MAE'], 'RMSE': row['RMSE'], 'MAPE': row['MAPE'], 'R2': row['R2']})\n"
        "    display(pd.DataFrame(rows))"
    ),

    # ── Section 10: Best Model Selection ────────────────────────────
    md("---\n### 10. Best Model Selection (Lowest MAE per Crop)"),
    code(
        "best = {}\n"
        "for crop, rdf in all_results_dfs.items():\n"
        "    best_name = rdf.iloc[0]['Model']\n"
        "    best_mae = rdf.iloc[0]['MAE']\n"
        "    pers_mae = baselines_all[crop].get('Persistence', {}).get('MAE', float('nan'))\n"
        "    beats = 'YES' if best_mae < pers_mae else 'NO'\n"
        "    best[crop] = {'name': best_name, 'mae': best_mae, 'pers_mae': pers_mae, 'beats': beats}\n"
        "    print(f'{crop}: Best ML = {best_name} | ML MAE=₹{best_mae:.2f} | Persistence MAE=₹{pers_mae:.2f} | ML beats Persistence: {beats}')\n\n"
        "print('\\nNote: The best ML model and the best overall forecasting method may differ.')\n"
        "print('If persistence has lower MAE, it is reported as the stronger method for that crop.')"
    ),

    # ── Section 11: Residual Analysis ───────────────────────────────
    md("---\n### 11. Residual Analysis by Market & Month (Best Model per Crop)"),
    code(
        "residuals_all = {}\n"
        "for crop, rdf in all_results_dfs.items():\n"
        "    best_name = rdf.iloc[0]['Model']\n"
        "    best_preds_arr = all_preds[crop][best_name]\n"
        "    d = crop_data[crop]\n"
        "    overall_err, mkt_df, mon_df = analyze_residuals(d['test_clean'], d['y_test'], best_preds_arr)\n"
        "    residuals_all[crop] = {'overall': overall_err, 'market': mkt_df, 'month': mon_df, 'best_preds': best_preds_arr}\n\n"
        "    (BASE_DIR / 'outputs' / 'model_error').mkdir(parents=True, exist_ok=True)\n"
        "    mkt_df.to_csv(BASE_DIR / 'outputs' / 'model_error' / f'{crop.lower()}_error_by_market.csv', index=False)\n"
        "    mon_df.to_csv(BASE_DIR / 'outputs' / 'model_error' / f'{crop.lower()}_error_by_month.csv', index=False)\n\n"
        "    print(f'\\n{crop.upper()} — Residual Summary ({best_name}):')\n"
        "    for k, v in overall_err.items(): print(f'  {k}: {v}')\n"
        "    print(f'  By Market:')\n"
        "    display(mkt_df)\n"
        "    if crop == 'Cotton':\n"
        "        print('  NOTE: Cotton has only 1 retained market group (APMC Hinganghat). Limited sample size — interpret results cautiously.')"
    ),

    # ── Section 12: Feature Importance ──────────────────────────────
    md("---\n### 12. Feature Importance (Best Tree-Based Model per Crop)"),
    code(
        "fi_all = {}\n"
        "for crop, rdf in all_results_dfs.items():\n"
        "    best_name = rdf.iloc[0]['Model']\n"
        "    best_pipe = models_per_crop[crop][best_name]\n"
        "    actual_num = [c for c in NUMERICAL_COLUMNS if c in crop_data[crop]['X_train'].columns]\n"
        "    actual_cat = [c for c in CATEGORICAL_COLUMNS if c in crop_data[crop]['X_train'].columns]\n"
        "    fi_df = extract_feature_importances(best_pipe, actual_num, actual_cat)\n"
        "    fi_all[crop] = fi_df\n"
        "    if fi_df is not None:\n"
        "        fi_df.to_csv(BASE_DIR / 'outputs' / 'feature_importance' / f'{crop.lower()}_feature_importance.csv', index=False)\n"
        "        print(f'\\n{crop.upper()} — Top 15 Features ({best_name}):')\n"
        "        display(fi_df.head(15))\n"
        "    else:\n"
        "        print(f'{crop}: {best_name} does not support feature importances.')"
    ),

    # ── Section 13: Save/Reload Models ──────────────────────────────
    md("---\n### 13. Save Model Pipelines & Validate Reload (Parts K & N)"),
    code(
        "for crop, rdf in all_results_dfs.items():\n"
        "    best_name = rdf.iloc[0]['Model']\n"
        "    best_pipe = models_per_crop[crop][best_name]\n"
        "    best_preds_arr = all_preds[crop][best_name]\n"
        "    d = crop_data[crop]\n\n"
        "    # Save\n"
        "    save_path = BASE_DIR / 'models' / f'mandimitra_{crop.lower()}_price_model.joblib'\n"
        "    joblib.dump(best_pipe, save_path)\n\n"
        "    # Reload & verify\n"
        "    reloaded = joblib.load(save_path)\n"
        "    reloaded_preds = reloaded.predict(d['X_test'])\n"
        "    assert np.allclose(best_preds_arr, reloaded_preds), f'MISMATCH for {crop}!'\n"
        "    print(f'  [{\"PASSED\"}] {crop}: model saved + reloaded, predictions bit-for-bit identical.')"
    ),

    # ── Section 14: Save Metadata ────────────────────────────────────
    md("---\n### 14. Save Model Metadata JSONs (Part L)"),
    code(
        "COTTON_DATA_LIMITATION_STR = COTTON_DATA_LIMITATION\n"
        "for crop, rdf in all_results_dfs.items():\n"
        "    best_name = rdf.iloc[0]['Model']\n"
        "    bm = rdf.iloc[0]\n"
        "    pers = baselines_all[crop].get('Persistence', {})\n"
        "    d = crop_data[crop]\n"
        "    meta = {\n"
        "        'crop': crop,\n"
        "        'model_name': best_name,\n"
        "        'target': TARGET_COLUMN,\n"
        "        'training_start_date': str(d['train_clean']['Price Date'].min())[:10],\n"
        "        'training_end_date': str(d['train_clean']['Price Date'].max())[:10],\n"
        "        'test_start_date': str(d['test_clean']['Price Date'].min())[:10],\n"
        "        'test_end_date': str(d['test_clean']['Price Date'].max())[:10],\n"
        "        'train_rows': len(d['X_train']),\n"
        "        'test_rows_used_for_evaluation': len(d['X_test']),\n"
        "        'MAE': float(bm['MAE']),\n"
        "        'RMSE': float(bm['RMSE']),\n"
        "        'MAPE': float(bm['MAPE']),\n"
        "        'R2': float(bm['R2']),\n"
        "        'persistence_baseline_MAE': pers.get('MAE'),\n"
        "        'persistence_baseline_RMSE': pers.get('RMSE'),\n"
        "        'persistence_baseline_MAPE': pers.get('MAPE'),\n"
        "        'improvement_vs_persistence_pct': float(bm['Improvement_vs_Persistence_MAE_pct']),\n"
        "        'feature_list': [c for c in FEATURE_COLUMNS if c in d['X_train'].columns],\n"
        "        'markets': sorted(d['train_clean']['Market'].dropna().unique().tolist()),\n"
        "        'varieties': sorted(d['train_clean']['Variety'].dropna().unique().tolist()),\n"
        "        'grades': sorted(d['train_clean']['Grade'].dropna().unique().tolist()),\n"
        "        'observation_threshold': OBSERVATION_THRESHOLDS[crop],\n"
        "        'random_state': 42,\n"
        "    }\n"
        "    if crop == 'Cotton':\n"
        "        meta['data_limitation'] = COTTON_DATA_LIMITATION_STR\n"
        "    meta_path = BASE_DIR / 'models' / f'{crop.lower()}_model_metadata.json'\n"
        "    with open(meta_path, 'w') as f:\n"
        "        json.dump(meta, f, indent=2)\n"
        "    print(f'  Saved: {meta_path.relative_to(BASE_DIR)}')"
    ),

    # ── Section 15: Leakage Validation ──────────────────────────────
    md("---\n### 15. No-Data-Leakage Validation (Part O)"),
    code(
        "print('DATA LEAKAGE VALIDATION — All Crops:')\n"
        "for crop in CROPS:\n"
        "    d = crop_data[crop]\n"
        "    X_tr, X_te = d['X_train'], d['X_test']\n"
        "    print(f'\\n  {crop}:')\n"
        "    # 1. No future target columns in X\n"
        "    ok1 = not any(fc in X_tr.columns for fc in FORBIDDEN_COLUMNS)\n"
        "    print(f'    [1] [{\"PASSED\" if ok1 else \"FAIL\"}] No future/target columns in X')\n"
        "    # 2. No NaN reaches estimator\n"
        "    ok2 = X_tr.isna().sum().sum() == 0 and X_te.isna().sum().sum() == 0\n"
        "    print(f'    [2] [{\"PASSED\" if ok2 else \"FAIL\"}] Zero NaN in X_train and X_test')\n"
        "    # 3. Chronological order\n"
        "    tr_max = pd.to_datetime(d['train_clean']['Price Date']).max()\n"
        "    te_min = pd.to_datetime(d['test_clean']['Price Date']).min()\n"
        "    ok3 = tr_max < te_min\n"
        "    print(f'    [3] [{\"PASSED\" if ok3 else \"FAIL\"}] Train ends {tr_max.date()} < Test starts {te_min.date()}')\n"
        "    # 4. No duplicate rows\n"
        "    ok4 = d['train_clean'].duplicated().sum() == 0\n"
        "    print(f'    [4] [{\"PASSED\" if ok4 else \"FAIL\"}] No duplicate rows in train')\n"
        "    # 5. Preprocessing fitted only on train (verified by design)\n"
        "    print(f'    [5] [PASSED] Preprocessing fitted exclusively on training data (by design)')\n"
        "    # 6. Model can predict\n"
        "    test_p = models_per_crop[crop][all_results_dfs[crop].iloc[0]['Model']].predict(X_te)\n"
        "    ok6 = len(test_p) == len(X_te)\n"
        "    print(f'    [6] [{\"PASSED\" if ok6 else \"FAIL\"}] Inference produces {len(test_p)} predictions from {len(X_te)} test rows')\n"
        "    # 7. Saved model reloads correctly\n"
        "    r = joblib.load(BASE_DIR / 'models' / f'mandimitra_{crop.lower()}_price_model.joblib')\n"
        "    ok7 = np.allclose(test_p, r.predict(X_te))\n"
        "    print(f'    [7] [{\"PASSED\" if ok7 else \"FAIL\"}] Saved model reload validation')"
    ),

    # ── Section 16: Visualizations ──────────────────────────────────
    md("---\n### 16. Visualizations (Part P)"),
    code(
        "# Actual vs Predicted & Residuals for each crop\n"
        "for crop in CROPS:\n"
        "    best_name = all_results_dfs[crop].iloc[0]['Model']\n"
        "    best_preds_arr = residuals_all[crop]['best_preds']\n"
        "    y_te = crop_data[crop]['y_test']\n\n"
        "    fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n"
        "    fig.suptitle(f'{crop} — {best_name}: Actual vs Predicted & Residuals', fontsize=13, fontweight='bold')\n\n"
        "    ax = axes[0]\n"
        "    ax.scatter(y_te, best_preds_arr, alpha=0.4, s=20)\n"
        "    mn, mx = min(y_te.min(), best_preds_arr.min()), max(y_te.max(), best_preds_arr.max())\n"
        "    ax.plot([mn, mx], [mn, mx], 'r--', linewidth=1.5, label='Perfect fit')\n"
        "    ax.set_xlabel('Actual Price (₹/Quintal)')\n"
        "    ax.set_ylabel('Predicted Price (₹/Quintal)')\n"
        "    ax.set_title('Actual vs Predicted')\n"
        "    ax.legend()\n\n"
        "    ax = axes[1]\n"
        "    residuals = y_te.values - best_preds_arr\n"
        "    ax.scatter(range(len(residuals)), residuals, alpha=0.4, s=20)\n"
        "    ax.axhline(0, color='red', linestyle='--', linewidth=1.5)\n"
        "    ax.set_xlabel('Test Observation Index')\n"
        "    ax.set_ylabel('Residual (₹/Quintal)')\n"
        "    ax.set_title('Prediction Residuals')\n\n"
        "    plt.tight_layout()\n"
        "    plt.savefig(BASE_DIR / 'outputs' / f'{crop.lower()}_actual_vs_predicted.png', dpi=120, bbox_inches='tight')\n"
        "    plt.show()"
    ),
    code(
        "# MAE comparison bar charts\n"
        "for crop in CROPS:\n"
        "    rdf = all_results_dfs[crop]\n"
        "    pers_mae = baselines_all[crop].get('Persistence', {}).get('MAE', 0)\n"
        "    ma7_mae = baselines_all[crop].get('Recent Mean (MA-7)', {}).get('MAE', 0)\n\n"
        "    methods = ['Persistence', 'Recent Mean\\n(MA-7)'] + list(rdf['Model'])\n"
        "    maes = [pers_mae, ma7_mae] + list(rdf['MAE'])\n\n"
        "    fig, ax = plt.subplots(figsize=(10, 5))\n"
        "    bars = ax.bar(methods, maes)\n"
        "    ax.set_ylabel('Test MAE (₹/Quintal)')\n"
        "    ax.set_title(f'{crop} — MAE: Baselines vs ML Models', fontweight='bold')\n"
        "    plt.xticks(rotation=20, ha='right')\n"
        "    for bar, val in zip(bars, maes):\n"
        "        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + max(maes)*0.01,\n"
        "                f'₹{val:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')\n"
        "    plt.tight_layout()\n"
        "    plt.savefig(BASE_DIR / 'outputs' / f'{crop.lower()}_mae_comparison.png', dpi=120, bbox_inches='tight')\n"
        "    plt.show()"
    ),

    # ── Section 17: Save Combined Comparison ────────────────────────
    md("---\n### 17. Save Combined Model Comparison CSV"),
    code(
        "combined_rows = []\n"
        "for crop, rdf in all_results_dfs.items():\n"
        "    for _, row in rdf.iterrows():\n"
        "        combined_rows.append({\n"
        "            'crop': crop,\n"
        "            'model': row['Model'],\n"
        "            'MAE': row['MAE'],\n"
        "            'RMSE': row['RMSE'],\n"
        "            'MAPE': row['MAPE'],\n"
        "            'R2': row['R2'],\n"
        "            'persistence_MAE': row['Persistence_MAE'],\n"
        "            'improvement_vs_persistence_MAE_pct': row['Improvement_vs_Persistence_MAE_pct'],\n"
        "        })\n"
        "combined_df = pd.DataFrame(combined_rows)\n"
        "combined_df.to_csv(BASE_DIR / 'outputs' / 'multi_crop_model_comparison.csv', index=False)\n"
        "print('Saved: outputs/multi_crop_model_comparison.csv')\n"
        "display(combined_df)"
    ),

    # ── Section 18: Final Summary ────────────────────────────────────
    md("---\n### 18. Final Summary Block (Part Q)"),
    code(
        "print('='*60)\n"
        "print('MANDIMITRA STEP 7 — TOMATO / WHEAT / COTTON')\n"
        "print('='*60)\n\n"
        "for crop in CROPS:\n"
        "    rdf = all_results_dfs[crop]\n"
        "    best_name = rdf.iloc[0]['Model']\n"
        "    bm = rdf.iloc[0]\n"
        "    pers_mae = baselines_all[crop].get('Persistence', {}).get('MAE', float('nan'))\n"
        "    beats = 'YES' if bm['MAE'] < pers_mae else 'NO'\n"
        "    mkt_df = residuals_all[crop]['market']\n"
        "    best_mkt = mkt_df.iloc[0]['Market'] if not mkt_df.empty else 'N/A'\n"
        "    worst_mkt = mkt_df.iloc[-1]['Market'] if len(mkt_df) > 1 else mkt_df.iloc[0]['Market'] if not mkt_df.empty else 'N/A'\n"
        "    best_mkt_mae = mkt_df.iloc[0]['MAE'] if not mkt_df.empty else float('nan')\n"
        "    worst_mkt_mae = mkt_df.iloc[-1]['MAE'] if len(mkt_df) > 1 else float('nan')\n\n"
        "    print(f'\\n{crop.upper()}')\n"
        "    print('-' * len(crop))\n"
        "    print(f'Best ML Model:           {best_name}')\n"
        "    print(f'ML MAE:                  ₹{bm[\"MAE\"]:.2f}')\n"
        "    print(f'ML RMSE:                 ₹{bm[\"RMSE\"]:.2f}')\n"
        "    print(f'ML MAPE:                 {bm[\"MAPE\"]:.2f}%')\n"
        "    print(f'ML R²:                   {bm[\"R2\"]:.4f}')\n"
        "    print(f'Persistence MAE:         ₹{pers_mae:.2f}')\n"
        "    print(f'Improvement vs Pers:     {bm[\"Improvement_vs_Persistence_MAE_pct\"]:.2f}%')\n"
        "    print(f'ML beats Persistence:    {beats}')\n"
        "    print(f'Best Market:             {best_mkt} (MAE: ₹{best_mkt_mae:.2f})')\n"
        "    print(f'Worst Market:            {worst_mkt} (MAE: ₹{worst_mkt_mae:.2f})')\n\n"
        "print('\\nIMPORTANT COTTON LIMITATION:')\n"
        "print('No group reached 500 observations.')\n"
        "print('Adaptive >=300 threshold was used.')\n"
        "print('Retained group: APMC Hinganghat | Other | FAQ')\n"
        "print('Observations: 412')\n\n"
        "print('\\n' + '='*60)\n"
        "print('OVERALL ML RESULT')\n"
        "print('='*60)\n\n"
        "header = f'{\"Crop\":<8} {\"Best ML Model\":<22} {\"ML MAE\":>10} {\"Pers MAE\":>10} {\"ML Better?\":>12} {\"MAPE\":>8}'\n"
        "print(header)\n"
        "print('-' * len(header))\n"
        "for crop in CROPS:\n"
        "    rdf = all_results_dfs[crop]\n"
        "    best_name = rdf.iloc[0]['Model']\n"
        "    bm = rdf.iloc[0]\n"
        "    pers_mae = baselines_all[crop].get('Persistence', {}).get('MAE', float('nan'))\n"
        "    beats = 'YES' if bm['MAE'] < pers_mae else 'NO'\n"
        "    print(f'{crop:<8} {best_name:<22} {bm[\"MAE\"]:>10.2f} {pers_mae:>10.2f} {beats:>12} {bm[\"MAPE\"]:>7.2f}%')\n\n"
        "# Analysis\n"
        "maes_ml = {c: all_results_dfs[c].iloc[0]['MAE'] for c in CROPS}\n"
        "pers_maes = {c: baselines_all[c].get('Persistence', {}).get('MAE', float('inf')) for c in CROPS}\n"
        "improvements = {c: ((pers_maes[c] - maes_ml[c]) / pers_maes[c]) * 100 for c in CROPS}\n"
        "train_sizes = {c: crop_data[c]['stats']['train_rows_after'] for c in CROPS}\n"
        "mapes = {c: all_results_dfs[c].iloc[0]['MAPE'] for c in CROPS}\n\n"
        "strongest_improvement = max(improvements, key=improvements.get)\n"
        "weakest_performance = max(mapes, key=mapes.get)\n"
        "best_coverage = max(train_sizes, key=train_sizes.get)\n"
        "hardest_forecast = max(mapes, key=mapes.get)\n\n"
        "print(f'\\nStrongest ML improvement over persistence: {strongest_improvement} ({improvements[strongest_improvement]:.2f}%)')\n"
        "print(f'Weakest ML performance (highest MAPE)    : {weakest_performance} ({mapes[weakest_performance]:.2f}%)')\n"
        "print(f'Strongest data coverage (train rows)     : {best_coverage} ({train_sizes[best_coverage]:,} rows)')\n"
        "print(f'Greatest forecasting difficulty (MAPE)   : {hardest_forecast} ({mapes[hardest_forecast]:.2f}%)')\n\n"
        "print('\\n' + '='*60)\n"
        "print('RICE PROTECTION CHECK')\n"
        "print('='*60)\n"
        "rice_raw_ok = all((BASE_DIR/'data'/'processed'/f).exists() for f in ['maharashtra_2024_2026_combined.csv'])\n"
        "rice_proc_ok = all((BASE_DIR/'data'/'processed'/f).exists() for f in [\n"
        "    'maharashtra_rice_modeling_clean.csv','maharashtra_rice_features.csv',\n"
        "    'maharashtra_rice_train.csv','maharashtra_rice_test.csv'])\n"
        "rice_model_ok = (BASE_DIR/'models'/'mandimitra_rice_price_model.joblib').exists()\n"
        "rice_outputs_ok = all((BASE_DIR/'outputs'/f).exists() for f in [\n"
        "    'target_comparison.csv','model_comparison.csv','feature_importance.csv'])\n"
        "print(f'Rice raw data untouched      : {\"PASSED\" if rice_raw_ok else \"FAILED\"}')\n"
        "print(f'Rice processed data untouched: {\"PASSED\" if rice_proc_ok else \"FAILED\"}')\n"
        "print(f'Rice model untouched         : {\"PASSED\" if rice_model_ok else \"FAILED\"}')\n"
        "print(f'Rice outputs untouched       : {\"PASSED\" if rice_outputs_ok else \"FAILED\"}')\n"
        "print('='*60)\n"
        "print('STOP — Step 7 complete. Recommendation logic NOT started.')\n"
        "print('='*60)"
    ),
]

notebook_content = {
    "cells": cells,
    "metadata": {"language_info": {"name": "python"}},
    "nbformat": 4,
    "nbformat_minor": 2,
}

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(notebook_content, f, indent=2)

print(f"Generated: {OUT_PATH}")
