"""Generate notebook 22 for MandiMitra price direction experiment."""
import json
from pathlib import Path

BASE_DIR = Path('.').resolve()
NB_DIR = BASE_DIR / "notebooks"
NB_DIR.mkdir(parents=True, exist_ok=True)

def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text}

def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": text}

nb22_cells = [
    md("# Step 22: MandiMitra ML V3 — Price Direction & Cross-Mandi Intelligence\n\n"
       "This experiment investigates whether machine learning can deliver more reliable decision support by predicting **Price Direction** (INCREASE, STABLE, DECREASE) over the next ~3 market observations rather than competing with persistence on exact point forecasts.\n\n"
       "### Key Principles\n"
       "- **Empirically Justified Movement Thresholds**: Set based on training set volatility (Rice: ±1.5%, Tomato: ±5.0%, Wheat: ±1.5%, Cotton: ±1.0%).\n"
       "- **Cross-Mandi Information**: Incorporates crop-wide price stats, market rank, spread, and momentum across active APMCs.\n"
       "- **Foundation Model Integration**: Tests Chronos-2 forecast signals as an input feature.\n"
       "- **Strict Causality**: Zero data leakage; only historical observations $\\le T$ are used.\n"
       "- **Decision Relevance**: Evaluates precision of 'WAIT' (Increase) and 'SELL' (Decrease/Stable) signals."),
    md("## 1. Run the Complete Direction Classification Benchmark"),
    code(
        "import sys\n"
        "from pathlib import Path\n"
        "import pandas as pd\n"
        "BASE_DIR = Path('..').resolve()\n"
        "if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))\n\n"
        "from src.direction_evaluation import run_direction_experiment\n"
        "df_comp, df_abl = run_direction_experiment()\n"
    ),
    md("## 2. Empirical Threshold Analysis"),
    code(
        "th_df = pd.read_csv(BASE_DIR / 'outputs' / 'final' / 'direction_threshold_analysis.csv')\n"
        "display(th_df)\n"
    ),
    md("## 3. Model Comparison Across Crops (Baselines vs. ML Classifiers)"),
    code(
        "comp_df = pd.read_csv(BASE_DIR / 'outputs' / 'final' / 'direction_model_comparison.csv')\n"
        "display(comp_df.sort_values(by=['crop', 'f1_macro'], ascending=[True, False]))\n"
    ),
    md("## 4. Feature Ablation Study (Historical vs Cross-Mandi vs Chronos-2)"),
    code(
        "abl_df = pd.read_csv(BASE_DIR / 'outputs' / 'final' / 'direction_ablation_results.csv')\n"
        "display(abl_df)\n"
    ),
    md("## 5. Market-Level Generalization Performance"),
    code(
        "mkt_df = pd.read_csv(BASE_DIR / 'outputs' / 'final' / 'direction_market_performance.csv')\n"
        "display(mkt_df.head(20))\n"
    ),
    md("## 6. Confusion Matrices"),
    code(
        "cm_df = pd.read_csv(BASE_DIR / 'outputs' / 'final' / 'direction_confusion_matrices.csv')\n"
        "display(cm_df)\n"
    ),
    md("## 7. Direction Inference Interface Demo"),
    code(
        "from src.direction_inference import predict_price_direction\n"
        "import json\n\n"
        "for crop, mkt, pr in [\n"
        "    ('rice', 'APMC Alibagh', 3500.0),\n"
        "    ('tomato', 'APMC Kamthi', 2770.0),\n"
        "    ('wheat', 'APMC Nagpur', 2650.0),\n"
        "    ('cotton', 'APMC Hinganghat', 7900.0)\n"
        "]:\n"
        "    res = predict_price_direction(crop, mkt, pr, '2026-09-04')\n"
        "    print(f'=== {crop.upper()} ===')\n"
        "    print(json.dumps(res, indent=2))\n"
    )
]

with open(NB_DIR / "22_price_direction_experiment.ipynb", "w") as f:
    json.dump({
        "cells": nb22_cells,
        "metadata": {"language_info": {"name": "python"}},
        "nbformat": 4,
        "nbformat_minor": 2
    }, f, indent=2)

print("Generated notebooks/22_price_direction_experiment.ipynb successfully.")
