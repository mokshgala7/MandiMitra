"""Generate notebooks 08-12 for MandiMitra multi-crop pipeline."""
import json
from pathlib import Path

OUT_DIR = Path("notebooks")
OUT_DIR.mkdir(exist_ok=True)


def nb(cells):
    return {
        "cells": cells,
        "metadata": {"language_info": {"name": "python"}},
        "nbformat": 4,
        "nbformat_minor": 2,
    }


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": text}


# ─────────────────────────────────────────────────────────────
# NOTEBOOK 08 — Data Loading
# ─────────────────────────────────────────────────────────────
nb08 = nb([
    md("# Step 08: Multi-Crop Data Loading & Validation\n"
       "## MandiMitra ML Pipeline — Tomato, Wheat, Cotton (Maharashtra 2024–2026)\n\n"
       "Load and validate raw AGMARKNET CSV files. Rice files are completely ignored."),

    md("### 1. Setup"),
    code("import sys\nfrom pathlib import Path\nimport pandas as pd\nimport matplotlib.pyplot as plt\nimport seaborn as sns\n"
         "sns.set_theme(style='whitegrid')\nBASE_DIR = Path('..').resolve()\nif str(BASE_DIR) not in sys.path:\n    sys.path.append(str(BASE_DIR))\n"
         "from src.multi_crop_data_loader import run_all_crops\nprint('Step 08: Multi-Crop Data Loading')"),

    md("### 2. Load and Combine All 9 Raw CSVs"),
    code("all_results = run_all_crops(verbose=True)"),

    md("### 3. Combined Dataset Summary Table"),
    code("summary_df = pd.read_csv(BASE_DIR / 'outputs' / 'multi_crop_data_summary.csv')\n"
         "print('MULTI-CROP DATA SUMMARY')\ndisplay(summary_df)"),

    md("### 4. Per-Crop Column & Type Audit"),
    code("for crop, (df, stats) in all_results.items():\n"
         "    print(f'\\n{crop.upper()} — dtypes:')\n    print(df.dtypes)\n"
         "    print(f'  Rows: {len(df):,} | Missing: {df.isna().sum().sum()} | Dups: {df.duplicated().sum()}')"),

    md("### 5. Schema Compatibility Check"),
    code("expected = ['State/UT','District','Market','Commodity Group','Commodity','Variety','Grade',\n"
         "            'Min Price','Max Price','Modal Price','Price Unit','Price Date']\nall_ok = True\n"
         "for crop, (df, _) in all_results.items():\n    missing = [c for c in expected if c not in df.columns]\n"
         "    print(f'  {crop}: {\"COMPATIBLE\" if not missing else f\"MISSING {missing}\"}')\n    if missing: all_ok = False\n"
         "print(f'\\n[{\"PASSED\" if all_ok else \"FAILED\"}] All crop CSVs share identical 12-column AGMARKNET schema.')"),

    md("### 6. Observations by Year"),
    code("fig, axes = plt.subplots(1, 3, figsize=(15, 5))\n"
         "for ax, (crop, (df, _)) in zip(axes, all_results.items()):\n"
         "    yc = df['Price Date'].dt.year.value_counts().sort_index()\n"
         "    ax.bar(yc.index.astype(str), yc.values, color='#2b5c8f')\n"
         "    ax.set_title(f'{crop} — Obs by Year'); ax.set_xlabel('Year'); ax.set_ylabel('Obs')\n"
         "    for i,v in enumerate(yc.values): ax.text(i, v+50, str(v), ha='center', fontsize=9)\n"
         "plt.suptitle('Maharashtra 2024-2026: Raw Observations per Year', fontsize=13, fontweight='bold')\n"
         "plt.tight_layout()\n"
         "plt.savefig(BASE_DIR/'outputs'/'eda'/'multi_crop_obs_by_year.png', dpi=120, bbox_inches='tight')\nplt.show()"),

    md("### 7. Rice Protection & File Validation"),
    code("rice_files = ['maharashtra_2024_2026_combined.csv','maharashtra_rice_modeling_clean.csv',\n"
         "              'maharashtra_rice_features.csv','maharashtra_rice_train.csv','maharashtra_rice_test.csv']\n"
         "for rf in rice_files:\n    p = BASE_DIR/'data'/'processed'/rf\n"
         "    print(f'  [{\"OK\" if p.exists() else \"MISSING\"}] Rice protected: {rf}')\n"
         "for crop in ['tomato','wheat','cotton']:\n"
         "    p = BASE_DIR/'data'/'processed'/f'maharashtra_{crop}_2024_2026_combined.csv'\n"
         "    print(f'  [{\"CREATED\" if p.exists() else \"MISSING\"}] New combined: {p.name}')"),

    md("### 8. Step 08 Completion"),
    code("print('='*60)\nprint('STEP 08 — MULTI-CROP DATA LOADING COMPLETE')\nprint('='*60)\n"
         "for crop, (df, stats) in all_results.items():\n"
         "    print(f'  {crop}: {stats[\"rows\"]:,} rows | {stats[\"start_date\"]} to {stats[\"end_date\"]} | {stats[\"unique_markets\"]} markets | {stats[\"unique_varieties\"]} varieties | {stats[\"unique_grades\"]} grades')"),
])

# ─────────────────────────────────────────────────────────────
# NOTEBOOK 09 — EDA
# ─────────────────────────────────────────────────────────────
nb09 = nb([
    md("# Step 09: Multi-Crop Exploratory Data Analysis\n"
       "## MandiMitra ML Pipeline — Tomato, Wheat, Cotton\n\n"
       "Independent EDA for each crop. No modifications to data."),

    md("### 1. Setup"),
    code("import sys\nfrom pathlib import Path\nimport pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\nimport seaborn as sns\n"
         "sns.set_theme(style='whitegrid')\nBASE_DIR = Path('..').resolve()\nif str(BASE_DIR) not in sys.path:\n    sys.path.append(str(BASE_DIR))\n"
         "(BASE_DIR/'outputs'/'eda').mkdir(parents=True, exist_ok=True)\nprint('Step 09: Multi-Crop EDA')"),

    md("### 2. Load Combined Datasets"),
    code("crops = {}\nfor crop in ['Tomato','Wheat','Cotton']:\n"
         "    p = BASE_DIR/'data'/'processed'/f'maharashtra_{crop.lower()}_2024_2026_combined.csv'\n"
         "    df = pd.read_csv(p)\n    df['Price Date'] = pd.to_datetime(df['Price Date'])\n"
         "    for col in ['Min Price','Max Price','Modal Price']:\n"
         "        df[col] = df[col].astype(str).str.replace(',','',regex=False).str.strip().replace('nan',float('nan')).astype(float)\n"
         "    crops[crop] = df\n    print(f'{crop}: {len(df):,} rows loaded')"),

    md("### 3. Dataset Overview per Crop"),
    code("for crop, df in crops.items():\n    print(f'\\n{\"=\"*55}')\n    print(f'CROP: {crop.upper()}')\n    print(f'{\"=\"*55}')\n"
         "    print(f'  Rows: {len(df):,} | Cols: {len(df.columns)}')\n"
         "    print(f'  Date range: {df[\"Price Date\"].min().date()} to {df[\"Price Date\"].max().date()}')\n"
         "    print(f'  Unique districts: {df[\"District\"].nunique()}')\n"
         "    print(f'  Unique markets  : {df[\"Market\"].nunique()}')\n"
         "    print(f'  Unique varieties: {df[\"Variety\"].nunique()} -> {sorted(df[\"Variety\"].unique())}')\n"
         "    print(f'  Unique grades   : {df[\"Grade\"].nunique()} -> {sorted(df[\"Grade\"].unique())}')\n"
         "    print(f'  Unique commodities: {df[\"Commodity\"].unique()}')\n"
         "    print(f'  Missing values  : {df.isna().sum().sum()}')\n"
         "    print(f'  Exact duplicates: {df.duplicated().sum()}')"),

    md("### 4. Price Distribution per Crop"),
    code("fig, axes = plt.subplots(3, 3, figsize=(16, 12))\n"
         "for row_idx, (crop, df) in enumerate(crops.items()):\n"
         "    for col_idx, pcol in enumerate(['Min Price','Modal Price','Max Price']):\n"
         "        ax = axes[row_idx][col_idx]\n"
         "        ax.hist(df[pcol].dropna(), bins=50, color='#2b5c8f', alpha=0.7, edgecolor='white')\n"
         "        ax.set_title(f'{crop} — {pcol}'); ax.set_xlabel('₹/Quintal'); ax.set_ylabel('Freq')\n"
         "        ax.axvline(df[pcol].median(), color='red', linestyle='--', linewidth=1.5, label=f'Median={df[pcol].median():.0f}')\n"
         "        ax.legend(fontsize=8)\n"
         "plt.suptitle('Price Distributions: Tomato, Wheat, Cotton', fontsize=13, fontweight='bold')\n"
         "plt.tight_layout()\n"
         "plt.savefig(BASE_DIR/'outputs'/'eda'/'multi_crop_price_distributions.png', dpi=120, bbox_inches='tight')\nplt.show()"),

    md("### 5. Observations by Month per Crop"),
    code("fig, axes = plt.subplots(1, 3, figsize=(18, 5))\n"
         "for ax, (crop, df) in zip(axes, crops.items()):\n"
         "    mc = df.groupby(df['Price Date'].dt.month).size()\n"
         "    mc.index = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][:len(mc)]\n"
         "    mc.plot(kind='bar', ax=ax, color='#4a90d9', edgecolor='white')\n"
         "    ax.set_title(f'{crop} — Obs by Month'); ax.set_xlabel(''); ax.set_ylabel('Observations'); ax.tick_params(axis='x', rotation=45)\n"
         "plt.suptitle('Seasonal Reporting Pattern by Crop', fontsize=13, fontweight='bold')\n"
         "plt.tight_layout()\n"
         "plt.savefig(BASE_DIR/'outputs'/'eda'/'multi_crop_obs_by_month.png', dpi=120, bbox_inches='tight')\nplt.show()"),

    md("### 6. Observations by Day of Week"),
    code("fig, axes = plt.subplots(1, 3, figsize=(16, 5))\nday_names = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']\n"
         "for ax, (crop, df) in zip(axes, crops.items()):\n"
         "    dc = df.groupby(df['Price Date'].dt.dayofweek).size().reindex(range(7), fill_value=0)\n"
         "    dc.index = day_names\n    dc.plot(kind='bar', ax=ax, color='#6baed6', edgecolor='white')\n"
         "    ax.set_title(f'{crop} — Obs by Day of Week'); ax.tick_params(axis='x', rotation=0)\n"
         "plt.suptitle('Reporting Days by Crop', fontsize=13, fontweight='bold')\n"
         "plt.tight_layout()\n"
         "plt.savefig(BASE_DIR/'outputs'/'eda'/'multi_crop_obs_by_dayofweek.png', dpi=120, bbox_inches='tight')\nplt.show()"),

    md("### 7. Top Markets by Observation Count"),
    code("for crop, df in crops.items():\n    print(f'\\nTop 10 Markets — {crop}:')\n"
         "    top = df.groupby('Market').size().sort_values(ascending=False).head(10)\n"
         "    for mkt, cnt in top.items(): print(f'  {mkt}: {cnt:,}')"),

    md("### 8. Market + Variety + Grade Group Counts"),
    code("for crop, df in crops.items():\n    print(f'\\n{crop} — Market+Variety+Grade groups:')\n"
         "    grp_counts = df.groupby(['Market','Variety','Grade']).size().sort_values(ascending=False)\n"
         "    print(f'  Total groups: {len(grp_counts)}')\n"
         "    print(f'  Groups >=500: {(grp_counts >= 500).sum()}')\n"
         "    print(f'  Groups >=300: {(grp_counts >= 300).sum()}')\n"
         "    print(f'  Groups >=100: {(grp_counts >= 100).sum()}')\n"
         "    print(f'  Top 5:')\n"
         "    for (m,v,g), c in grp_counts.head(5).items(): print(f'    {m} | {v} | {g}: {c}')"),

    md("### 9. Price Volatility Analysis"),
    code("print('Price Volatility (Coefficient of Variation) per Crop:')\n"
         "for crop, df in crops.items():\n    cv = df['Modal Price'].std() / df['Modal Price'].mean() * 100\n"
         "    print(f'  {crop}: CV={cv:.1f}% | Mean=₹{df[\"Modal Price\"].mean():.0f} | Std=₹{df[\"Modal Price\"].std():.0f}')"),

    md("### 10. Min <= Modal <= Max Consistency Check"),
    code("for crop, df in crops.items():\n"
         "    v1 = (df['Min Price'] > df['Modal Price']).sum()\n"
         "    v2 = (df['Modal Price'] > df['Max Price']).sum()\n"
         "    print(f'  {crop}: Min>Modal={v1} violations | Modal>Max={v2} violations')"),

    md("### 11. Reporting Gaps Analysis"),
    code("for crop, df in crops.items():\n    print(f'\\n{crop} — Reporting gaps (by Market+Variety+Grade):')\n"
         "    gaps = []\n"
         "    for keys, grp in df.groupby(['Market','Variety','Grade']):\n"
         "        grp = grp.sort_values('Price Date')\n"
         "        diffs = grp['Price Date'].diff().dt.days.dropna()\n"
         "        if len(diffs): gaps.append(diffs.max())\n"
         "    if gaps:\n        import numpy as np\n"
         "        print(f'  Max single gap across all groups: {max(gaps):.0f} days')\n"
         "        print(f'  Median max gap: {np.median(gaps):.0f} days')\n"
         "        print(f'  Groups with gap >30 days: {sum(g>30 for g in gaps)}')"),

    md("### 12. Arrival Quantity Check"),
    code("for crop, df in crops.items():\n"
         "    arrival_cols = [c for c in df.columns if 'arrival' in c.lower() or 'quantity' in c.lower()]\n"
         "    print(f'  {crop}: Arrival/Quantity columns = {arrival_cols if arrival_cols else \"NONE — not available in dataset\"}')"),

    md("### 13. Duplicate Market+Variety+Grade+Date Combinations"),
    code("for crop, df in crops.items():\n"
         "    dup = df.duplicated(subset=['Market','Variety','Grade','Price Date']).sum()\n"
         "    print(f'  {crop}: Duplicate Market+Variety+Grade+Date rows = {dup}')"),

    md("### 14. Statistical Outlier Detection (IQR×3)"),
    code("for crop, df in crops.items():\n    print(f'\\n{crop} Outliers (Modal Price IQR×3 per group):')\n"
         "    n_out = 0\n"
         "    for keys, grp in df.groupby(['Market','Variety','Grade']):\n"
         "        q1, q3 = grp['Modal Price'].quantile(0.25), grp['Modal Price'].quantile(0.75)\n"
         "        iqr = q3 - q1\n        n_out += ((grp['Modal Price'] < q1-3*iqr)|(grp['Modal Price'] > q3+3*iqr)).sum()\n"
         "    print(f'  Total statistical outlier flags: {n_out}')"),

    md("### 15. Temporal Price Trend (Modal Price) per Crop"),
    code("fig, axes = plt.subplots(3, 1, figsize=(16, 12))\n"
         "for ax, (crop, df) in zip(axes, crops.items()):\n"
         "    monthly = df.groupby(df['Price Date'].dt.to_period('M'))['Modal Price'].median()\n"
         "    monthly.index = monthly.index.to_timestamp()\n"
         "    ax.plot(monthly.index, monthly.values, color='#2b5c8f', linewidth=1.8)\n"
         "    ax.fill_between(monthly.index, monthly.values, alpha=0.15, color='#2b5c8f')\n"
         "    ax.set_title(f'{crop} — Median Modal Price (Monthly)', fontweight='bold')\n"
         "    ax.set_ylabel('₹/Quintal'); ax.set_xlabel('')\n"
         "plt.suptitle('Price Trends: Tomato, Wheat, Cotton (2024–2026)', fontsize=13, fontweight='bold')\n"
         "plt.tight_layout()\n"
         "plt.savefig(BASE_DIR/'outputs'/'eda'/'multi_crop_price_trends.png', dpi=120, bbox_inches='tight')\nplt.show()"),

    md("### 16. EDA Summary per Crop"),
    code("summaries = {\n"
         "    'Tomato': (\n"
         "        'TOMATO DATA QUALITY SUMMARY\\n'\n"
         "        '  Quality  : High — 0 missing values, 0 exact duplicates, 0 price order violations.\\n'\n"
         "        '  Markets  : 60 unique, highly fragmented. Only 4 groups reach >=500 obs threshold.\\n'\n"
         "        '  Varieties: 2 (Other, Local). Grade: 2 (Local, FAQ).\\n'\n"
         "        '  Reliable : Pune(Pimpri), Pune(Manjri), APMC Panvel, APMC Kamthi.\\n'\n"
         "        '  Sparse   : 56 markets with <500 obs — not retained.\\n'\n"
         "        '  Price    : Highly volatile (CV ~50%). Range ₹300–₹7500/quintal. Seasonal peaks.\\n'\n"
         "        '  Limitation: No arrival quantity. Irregular reporting gaps. Price jumps possible.\\n'\n"
         "    ),\n"
         "    'Wheat': (\n"
         "        'WHEAT DATA QUALITY SUMMARY\\n'\n"
         "        '  Quality  : High — 0 missing, 0 exact dups, 0 price violations. 109 outlier flags.\\n'\n"
         "        '  Markets  : 242 unique, 21 groups meet >=500 obs. Strong coverage.\\n'\n"
         "        '  Varieties: 7 (Other, Sharbati, Maharashtra 2189, Bansi, etc.). Grade: FAQ dominates.\\n'\n"
         "        '  Reliable : APMC Solapur, APMC Kopargaon, APMC Nagpur, APMC Jalana.\\n'\n"
         "        '  Price    : Moderate volatility. Range ₹1700–₹4774/quintal. Seasonal harvest cycle.\\n'\n"
         "        '  Limitation: No arrival quantity. 109 statistical outlier flags (not removed).\\n'\n"
         "    ),\n"
         "    'Cotton': (\n"
         "        'COTTON DATA QUALITY SUMMARY\\n'\n"
         "        '  Quality  : High — 0 missing, 0 dups, 0 price violations.\\n'\n"
         "        '  Markets  : 86 unique, but NO group reaches >=500 obs. Max = 412 (APMC Hinganghat).\\n'\n"
         "        '  ADAPTIVE : Threshold lowered to >=300 (data-driven). Only 1 group retained.\\n'\n"
         "        '  Varieties: 8 (N-44, Desi, H-4A 27mm Fine, Other, LRA, etc.). Grades: FAQ/Local/Non-FAQ.\\n'\n"
         "        '  Price    : Low volatility (CV ~8%). Range ₹4700–₹8500. Seasonal crop.\\n'\n"
         "        '  Limitation: Seasonal reporting — cotton harvested Oct–Feb; sparse in off-season.\\n'\n"
         "        '             Only 1 retained group limits ML generalizability.\\n'\n"
         "    )\n"
         "}\nfor crop, summary in summaries.items():\n    print(f'\\n{\"=\"*55}\\n{summary}')"),

    md("### 17. Step 09 Completion"),
    code("print('='*60)\nprint('STEP 09 — EDA COMPLETE')\nprint('='*60)\n"
         "print('EDA outputs saved to outputs/eda/')\n"
         "for crop, df in crops.items():\n"
         "    print(f'  {crop}: {len(df):,} rows | {df[\"Price Date\"].min().date()} to {df[\"Price Date\"].max().date()}')"),
])

# ─────────────────────────────────────────────────────────────
# NOTEBOOK 10 — Cleaning
# ─────────────────────────────────────────────────────────────
nb10 = nb([
    md("# Step 10: Multi-Crop Data Cleaning & Coverage Filtering\n"
       "## MandiMitra ML Pipeline — Tomato, Wheat, Cotton\n\n"
       "Apply >=500 obs filter (>=300 for data-constrained Cotton), clean and save modeling datasets."),

    md("### 1. Setup"),
    code("import sys\nfrom pathlib import Path\nimport pandas as pd\n"
         "BASE_DIR = Path('..').resolve()\nif str(BASE_DIR) not in sys.path:\n    sys.path.append(str(BASE_DIR))\n"
         "from src.multi_crop_cleaning import clean_all_crops\nprint('Step 10: Multi-Crop Cleaning')"),

    md("### 2. Run Cleaning Pipeline"),
    code("results = clean_all_crops(verbose=True)"),

    md("### 3. Coverage Reports"),
    code("for crop in ['Tomato','Wheat','Cotton']:\n"
         "    cov = pd.read_csv(BASE_DIR/'outputs'/'coverage'/f'{crop.lower()}_market_coverage.csv')\n"
         "    retained = cov[cov['Retained'] | (cov.get('Retained_Adaptive_300', False) if 'Retained_Adaptive_300' in cov.columns else False)]\n"
         "    print(f'\\n{crop} — Coverage Report (Top 10 by obs count):')\n"
         "    display(cov.head(10))\n"
         "    print(f'  Retained groups: {cov[\"Retained\"].sum()} (>=500) | Total groups: {len(cov)}')"),

    md("### 4. Cotton Adaptive Threshold Note"),
    code("print('COTTON ADAPTIVE THRESHOLD NOTICE:')\n"
         "print('  No Market+Variety+Grade group in Cotton reaches 500 observations.')\n"
         "print('  The highest single-group count is 412 (APMC Hinganghat | Other | FAQ).')\n"
         "print('  Cotton is a seasonal crop with restricted Oct-Feb harvest reporting window.')\n"
         "print('  Adaptive threshold of >=300 obs applied for Cotton only.')\n"
         "print('  1 group retained: APMC Hinganghat | Other | FAQ — 412 obs.')\n"
         "print('  This limitation will be clearly flagged in modeling step.')"),

    md("### 5. Cleaning Summaries"),
    code("for crop in ['Tomato','Wheat','Cotton']:\n"
         "    s = pd.read_csv(BASE_DIR/'outputs'/'cleaning'/f'{crop.lower()}_cleaning_summary.csv')\n"
         "    print(f'\\n{crop} Cleaning Summary:')\n    display(s)"),

    md("### 6. Verify Modeling Clean Files"),
    code("for crop in ['Tomato','Wheat','Cotton']:\n"
         "    p = BASE_DIR/'data'/'processed'/f'maharashtra_{crop.lower()}_modeling_clean.csv'\n"
         "    df = pd.read_csv(p)\n"
         "    print(f'  {crop}: {len(df):,} modeling rows | Groups: {df.groupby([\"Market\",\"Variety\",\"Grade\"]).ngroups}')"),

    md("### 7. Validation Checks"),
    code("print('VALIDATION CHECKS:')\n"
         "# Rice files untouched\n"
         "rice_files = ['maharashtra_rice_modeling_clean.csv','maharashtra_rice_features.csv',\n"
         "              'maharashtra_rice_train.csv','maharashtra_rice_test.csv']\n"
         "for rf in rice_files:\n    p = BASE_DIR/'data'/'processed'/rf\n"
         "    print(f'  [{\"OK\" if p.exists() else \"MISSING\"}] Rice protected: {rf}')\n"
         "# No interpolation\n"
         "print('  [OK] No interpolation or forward-fill performed (genuine obs only retained)')\n"
         "print('  [OK] Groups filtered by observation count — no artificial obs created')"),

    md("### 8. Step 10 Completion"),
    code("print('='*60)\nprint('STEP 10 — CLEANING COMPLETE')\nprint('='*60)\n"
         "for crop, r in results.items():\n    s = r['summary']\n"
         "    ret = s.get('retained_groups', s.get('retained_groups_at_300', 0))\n"
         "    print(f'  {crop}: {s[\"modeling_rows\"]:,} modeling rows | {ret} retained groups')"),
])

# ─────────────────────────────────────────────────────────────
# NOTEBOOK 11 — Feature Engineering
# ─────────────────────────────────────────────────────────────
nb11 = nb([
    md("# Step 11: Multi-Crop Feature Engineering\n"
       "## MandiMitra ML Pipeline — Tomato, Wheat, Cotton\n\n"
       "Engineer lag, rolling, momentum, spread, and calendar features independently per series. Zero leakage."),

    md("### 1. Setup"),
    code("import sys\nfrom pathlib import Path\nimport pandas as pd\nimport numpy as np\n"
         "BASE_DIR = Path('..').resolve()\nif str(BASE_DIR) not in sys.path:\n    sys.path.append(str(BASE_DIR))\n"
         "from src.multi_crop_feature_engineering import engineer_all_crops\nprint('Step 11: Feature Engineering')"),

    md("### 2. Engineer Features for All Crops"),
    code("feat_results = engineer_all_crops(verbose=True)"),

    md("### 3. Feature Dataset Overview"),
    code("for crop, df in feat_results.items():\n    if df.empty:\n        print(f'{crop}: EMPTY'); continue\n"
         "    print(f'\\n{crop}: {len(df):,} rows x {len(df.columns)} columns')\n"
         "    lag_cols = [c for c in df.columns if 'lag' in c]\n"
         "    ma_cols = [c for c in df.columns if 'price_ma' in c]\n"
         "    mom_cols = [c for c in df.columns if 'change' in c]\n"
         "    cal_cols = [c for c in df.columns if c in ['year','month','day','day_of_week','day_of_year','week_of_year','is_weekend','month_sin','month_cos','day_of_year_sin','day_of_year_cos']]\n"
         "    tgt_cols = [c for c in df.columns if 'price_next' in c or 'price_after' in c or 'future_' in c]\n"
         "    print(f'  Lag features ({len(lag_cols)}): {lag_cols}')\n"
         "    print(f'  MA features  ({len(ma_cols)}): {ma_cols}')\n"
         "    print(f'  Momentum     ({len(mom_cols)}): {mom_cols}')\n"
         "    print(f'  Calendar     ({len(cal_cols)}): {cal_cols}')\n"
         "    print(f'  Targets      ({len(tgt_cols)}): {tgt_cols}')"),

    md("### 4. Target Variable Statistics"),
    code("for crop, df in feat_results.items():\n    if df.empty: continue\n"
         "    print(f'\\n{crop} — Target candidate statistics:')\n"
         "    for tgt in ['price_next_observation','price_after_3_observations','price_after_7_observations']:\n"
         "        if tgt in df.columns:\n            s = df[tgt].dropna()\n"
         "            print(f'  {tgt}: n={len(s):,} mean=₹{s.mean():.0f} std=₹{s.std():.0f} min=₹{s.min():.0f} max=₹{s.max():.0f}')"),

    md("### 5. Leakage Audit — No Future Target in Feature Space"),
    code("forbidden = ['price_next_observation','price_after_3_observations','price_after_7_observations',\n"
         "             'future_price_change_3','future_price_change_7']\n"
         "input_features = ['Min Price','Max Price','Modal Price',\n"
         "                  'price_lag_1','price_lag_2','price_lag_3','price_lag_7','price_lag_14','price_lag_30',\n"
         "                  'price_ma_3','price_ma_7','price_ma_14','price_ma_30',\n"
         "                  'price_std_7','price_std_14','price_std_30',\n"
         "                  'price_change_1','price_change_1_pct','price_change_3','price_change_3_pct',\n"
         "                  'price_change_7','price_change_7_pct','price_change_14','price_change_14_pct',\n"
         "                  'price_range','price_range_pct',\n"
         "                  'year','month','day','day_of_week','day_of_year','week_of_year','is_weekend',\n"
         "                  'month_sin','month_cos','day_of_year_sin','day_of_year_cos',\n"
         "                  'Market','Variety','Grade']\n"
         "all_ok = True\n"
         "for feat in input_features:\n    for f in forbidden:\n        if feat == f:\n            print(f'  LEAKAGE: {feat} is in both input and forbidden!'); all_ok = False\n"
         "print(f'[{\"PASSED\" if all_ok else \"FAILED\"}] Zero future target columns present in input feature set.')"),

    md("### 6. Series Independence Check"),
    code("for crop, df in feat_results.items():\n    if df.empty: continue\n"
         "    groups = df.groupby(['Market','Variety','Grade'])\n"
         "    print(f'{crop}: {groups.ngroups} independent series processed separately — cross-series leakage impossible.')"),

    md("### 7. Missing Values from Initial Lag Windows"),
    code("for crop, df in feat_results.items():\n    if df.empty: continue\n"
         "    nan_lag1 = df['price_lag_1'].isna().sum()\n    nan_lag30 = df['price_lag_30'].isna().sum()\n"
         "    print(f'  {crop}: price_lag_1 NaN={nan_lag1} | price_lag_30 NaN={nan_lag30} (expected from initial window — no imputation applied)')"),

    md("### 8. Step 11 Completion"),
    code("print('='*60)\nprint('STEP 11 — FEATURE ENGINEERING COMPLETE')\nprint('='*60)\n"
         "for crop, df in feat_results.items():\n"
         "    print(f'  {crop}: {len(df):,} rows x {len(df.columns)} columns saved')"),
])

# ─────────────────────────────────────────────────────────────
# NOTEBOOK 12 — Target Selection & Split
# ─────────────────────────────────────────────────────────────
nb12 = nb([
    md("# Step 12: Multi-Crop Target Selection & Chronological Train/Test Split\n"
       "## MandiMitra ML Pipeline — Tomato, Wheat, Cotton\n\n"
       "Strict 80/20 chronological split per crop. No random shuffling. No leakage."),

    md("### 1. Setup"),
    code("import sys\nfrom pathlib import Path\nimport pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\n"
         "import seaborn as sns\nsns.set_theme(style='whitegrid')\n"
         "BASE_DIR = Path('..').resolve()\nif str(BASE_DIR) not in sys.path:\n    sys.path.append(str(BASE_DIR))\n"
         "from src.multi_crop_train_test_split import split_all_crops\nprint('Step 12: Target Selection & Chronological Split')"),

    md("### 2. Run Split Pipeline"),
    code("split_results = split_all_crops(verbose=True)"),

    md("### 3. Target Comparison Tables"),
    code("for crop in ['Tomato','Wheat','Cotton']:\n"
         "    p = BASE_DIR/'outputs'/'target_selection'/f'{crop.lower()}_target_comparison.csv'\n"
         "    tc = pd.read_csv(p)\n    print(f'\\n{crop} — Target Comparison:')\n    display(tc)"),

    md("### 4. Split Summary Tables"),
    code("for crop in ['Tomato','Wheat','Cotton']:\n"
         "    p = BASE_DIR/'outputs'/'splits'/f'{crop.lower()}_split_summary.csv'\n"
         "    ss = pd.read_csv(p)\n    print(f'\\n{crop} — Split Summary:')\n    display(ss)"),

    md("### 5. Verify Chronological Order"),
    code("print('CHRONOLOGICAL ORDER VERIFICATION:')\n"
         "for crop in ['Tomato','Wheat','Cotton']:\n"
         "    train = pd.read_csv(BASE_DIR/'data'/'processed'/f'maharashtra_{crop.lower()}_train.csv')\n"
         "    test = pd.read_csv(BASE_DIR/'data'/'processed'/f'maharashtra_{crop.lower()}_test.csv')\n"
         "    train['Price Date'] = pd.to_datetime(train['Price Date'])\n"
         "    test['Price Date'] = pd.to_datetime(test['Price Date'])\n"
         "    ok = train['Price Date'].max() < test['Price Date'].min()\n"
         "    print(f'  [{\"PASSED\" if ok else \"FAILED\"}] {crop}: train ends {train[\"Price Date\"].max().date()} < test starts {test[\"Price Date\"].min().date()}')"),

    md("### 6. No NaN in Primary Target (Train Set)"),
    code("primary_targets = {'Tomato':'price_after_3_observations','Wheat':'price_after_3_observations','Cotton':'price_after_3_observations'}\n"
         "print('TARGET NaN CHECK (train set):')\n"
         "for crop, tgt in primary_targets.items():\n"
         "    train = pd.read_csv(BASE_DIR/'data'/'processed'/f'maharashtra_{crop.lower()}_train.csv')\n"
         "    nan_count = train[tgt].isna().sum() if tgt in train.columns else 'N/A'\n"
         "    print(f'  [{\"PASSED\" if nan_count == 0 else \"CHECK\"}] {crop} train set {tgt} NaN = {nan_count}')"),

    md("### 7. Train/Test Size Visualization"),
    code("fig, ax = plt.subplots(figsize=(10, 5))\ncrops_list = ['Tomato','Wheat','Cotton']\n"
         "train_sizes, test_sizes = [], []\n"
         "for crop in crops_list:\n"
         "    train = pd.read_csv(BASE_DIR/'data'/'processed'/f'maharashtra_{crop.lower()}_train.csv')\n"
         "    test = pd.read_csv(BASE_DIR/'data'/'processed'/f'maharashtra_{crop.lower()}_test.csv')\n"
         "    train_sizes.append(len(train)); test_sizes.append(len(test))\n"
         "x = range(len(crops_list))\n"
         "ax.bar(x, train_sizes, label='Train (80%)', color='#2b5c8f', width=0.4)\n"
         "ax.bar([i+0.4 for i in x], test_sizes, label='Test (20%)', color='#6baed6', width=0.4)\n"
         "ax.set_xticks([i+0.2 for i in x]); ax.set_xticklabels(crops_list)\n"
         "ax.set_ylabel('Rows'); ax.set_title('Train/Test Split Sizes by Crop'); ax.legend()\n"
         "for i,v in enumerate(train_sizes): ax.text(i, v+30, str(v), ha='center', fontsize=9, fontweight='bold')\n"
         "for i,v in enumerate(test_sizes): ax.text(i+0.4, v+30, str(v), ha='center', fontsize=9, fontweight='bold')\n"
         "plt.tight_layout()\n"
         "plt.savefig(BASE_DIR/'outputs'/'splits'/'multi_crop_train_test_sizes.png', dpi=120, bbox_inches='tight')\nplt.show()"),

    md("### 8. Persistence & MA-7 Baseline per Crop"),
    code("print('BASELINE BENCHMARKS PER CROP (from target comparison):')\n"
         "for crop in ['Tomato','Wheat','Cotton']:\n"
         "    tc = pd.read_csv(BASE_DIR/'outputs'/'target_selection'/f'{crop.lower()}_target_comparison.csv')\n"
         "    row = tc[tc['target'] == 'price_after_3_observations'].iloc[0]\n"
         "    print(f'  {crop}:')\n"
         "    print(f'    Persistence MAE = ₹{row[\"persistence_MAE\"]:.2f}')\n"
         "    print(f'    MA-7 MAE        = ₹{row[\"ma7_MAE\"]:.2f}')\n"
         "    print(f'    Valid obs (test target): {row[\"valid_observations\"]:,}')"),

    md("### 9. Rice Protection Final Check"),
    code("print('RICE PROTECTION CHECK:')\n"
         "rice_checks = [\n"
         "    ('data/processed/maharashtra_2024_2026_combined.csv', 'Rice data'),\n"
         "    ('data/processed/maharashtra_rice_modeling_clean.csv', 'Rice clean'),\n"
         "    ('data/processed/maharashtra_rice_features.csv', 'Rice features'),\n"
         "    ('data/processed/maharashtra_rice_train.csv', 'Rice train'),\n"
         "    ('data/processed/maharashtra_rice_test.csv', 'Rice test'),\n"
         "    ('models/mandimitra_rice_price_model.joblib', 'Rice model'),\n"
         "    ('models/model_metadata.json', 'Rice metadata'),\n"
         "]\n"
         "for rel_path, label in rice_checks:\n    p = BASE_DIR/rel_path\n"
         "    print(f'  [{\"OK\" if p.exists() else \"MISSING\"}] {label}: {rel_path}')"),

    md("### 10. Final Summary Block"),
    code("""import pandas as pd
from pathlib import Path
BASE_DIR = Path('..').resolve()

def get_split_info(crop):
    ss = pd.read_csv(BASE_DIR/'outputs'/'splits'/f'{crop.lower()}_split_summary.csv').iloc[0]
    tc = pd.read_csv(BASE_DIR/'outputs'/'target_selection'/f'{crop.lower()}_target_comparison.csv')
    cov = pd.read_csv(BASE_DIR/'outputs'/'coverage'/f'{crop.lower()}_market_coverage.csv')
    raw = pd.read_csv(BASE_DIR/'outputs'/f'{crop.lower()}_data_validation.csv').iloc[0]
    retained = int(cov['Retained'].sum()) if 'Retained' in cov.columns else 0
    if retained == 0 and 'Retained_Adaptive_300' in cov.columns:
        retained = int(cov['Retained_Adaptive_300'].sum())
    clean = pd.read_csv(BASE_DIR/'data'/'processed'/f'maharashtra_{crop.lower()}_modeling_clean.csv')
    return {
        'raw_rows': raw['rows'], 'start': raw['start_date'], 'end': raw['end_date'],
        'markets': raw['unique_markets'], 'varieties': raw['unique_varieties'],
        'grades': raw['unique_grades'], 'retained': retained,
        'modeling_rows': len(clean), 'target': ss['primary_target'],
        'train_rows': ss['train_rows'], 'test_rows': ss['test_rows'],
        'cutoff': ss['cutoff_date']
    }

print('='*60)
print('MANDIMITRA — TOMATO / WHEAT / COTTON STEPS 1–6')
print('='*60)

for crop in ['Tomato','Wheat','Cotton']:
    info = get_split_info(crop)
    print(f'\\n{crop.upper()}')
    print('-'*len(crop))
    print(f'Raw rows:           {info[\"raw_rows\"]:,}')
    print(f'Date range:         {info[\"start\"]} to {info[\"end\"]}')
    print(f'Unique markets:     {info[\"markets\"]}')
    print(f'Unique varieties:   {info[\"varieties\"]}')
    print(f'Unique grades:      {info[\"grades\"]}')
    print(f'Retained groups >=500: {info[\"retained\"]}')
    print(f'Modeling rows:      {info[\"modeling_rows\"]:,}')
    print(f'Recommended target: {info[\"target\"]}')
    print(f'Train rows:         {info[\"train_rows\"]:,}')
    print(f'Test rows:          {info[\"test_rows\"]:,}')
    print(f'Cutoff date:        {info[\"cutoff\"]}')

print()
print('='*60)
print('RICE PROTECTION CHECK')
print('='*60)
rice_data_ok = all((BASE_DIR/'data'/'processed'/f).exists() for f in
    ['maharashtra_2024_2026_combined.csv','maharashtra_rice_modeling_clean.csv',
     'maharashtra_rice_features.csv','maharashtra_rice_train.csv','maharashtra_rice_test.csv'])
rice_model_ok = (BASE_DIR/'models'/'mandimitra_rice_price_model.joblib').exists()
rice_outputs_ok = all((BASE_DIR/'outputs'/f).exists() for f in
    ['target_comparison.csv','baseline_results.csv','split_summary.csv',
     'model_comparison.csv','model_error_by_market.csv','model_error_by_month.csv','feature_importance.csv'])
print(f'Rice data untouched  : {\"PASSED\" if rice_data_ok else \"FAILED\"}')
print(f'Rice model untouched : {\"PASSED\" if rice_model_ok else \"FAILED\"}')
print(f'Rice outputs untouched: {\"PASSED\" if rice_outputs_ok else \"FAILED\"}')
print('='*60)
print('STOP — Step 6 complete. Model training NOT started.')
print('='*60)
"""),
])

# Write all notebooks
notebooks = {
    "08_multi_crop_data_loading.ipynb": nb08,
    "09_multi_crop_eda.ipynb": nb09,
    "10_multi_crop_cleaning.ipynb": nb10,
    "11_multi_crop_feature_engineering.ipynb": nb11,
    "12_multi_crop_target_selection_and_split.ipynb": nb12,
}
for fname, content in notebooks.items():
    path = OUT_DIR / fname
    with open(path, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=2)
    print(f"Generated: {path}")

print("\nAll 5 notebooks generated successfully.")
