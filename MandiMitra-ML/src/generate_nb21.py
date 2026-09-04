"""Generate notebook 21 for MandiMitra Chronos-2 experiment."""
import json
from pathlib import Path

BASE_DIR = Path('.').resolve()
NB_DIR = BASE_DIR / "notebooks"
NB_DIR.mkdir(parents=True, exist_ok=True)

def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text}

def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": text}

nb21_cells = [
    md("# Step 21: Amazon Chronos-2 Zero-Shot Foundation Model Experiment\n\n"
       "This notebook evaluates **Amazon Chronos-2** (`amazon/chronos-2`) as a zero-shot, in-context time series forecasting foundation model for APMC mandi price prediction across 4 crops:\n"
       "1. **Rice**\n"
       "2. **Tomato**\n"
       "3. **Wheat**\n"
       "4. **Cotton**\n\n"
       "### Objectives & Guarantees\n"
       "- **Horizon**: Primary forecast horizon is 3 observations ahead ($t+3$), aligning with the validated project target `price_after_3_observations`.\n"
       "- **Zero Data Leakage**: At any forecast cutoff date $T$, the context series only contains observations $\\le T$.\n"
       "- **Baselines**: Compared directly against the **Persistence Baseline** ($y_{t+3} = y_t$), **7-Observation Moving Average (MA-7)**, and the previous best **Tabular ML Models**.\n"
       "- **Decision Rule**: Chronos-2 becomes the production forecasting method **only** if it genuinely outperforms persistence on the untouched held-out test sets."),
    code(
        "import sys\n"
        "from pathlib import Path\n"
        "import pandas as pd\n"
        "BASE_DIR = Path('..').resolve()\n"
        "if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))\n\n"
        "from src.chronos_forecast import get_chronos_pipeline\n"
        "pipeline = get_chronos_pipeline(device='cpu')\n"
        "print('Chronos-2 Pipeline Ready!')\n"
    ),
    md("## 1. Run Chronological Evaluation Across All 4 Crops"),
    code(
        "from src.chronos_evaluation import run_full_chronos_experiment\n"
        "summary_df = run_full_chronos_experiment()\n"
        "display(summary_df)\n"
    ),
    md("## 2. Model Performance Comparison vs Baselines"),
    code(
        "comp_df = pd.read_csv(BASE_DIR / 'outputs' / 'final' / 'chronos2_model_comparison.csv')\n"
        "display(comp_df)\n"
    ),
    md("## 3. Market-Level Generalization Performance"),
    code(
        "mkt_df = pd.read_csv(BASE_DIR / 'outputs' / 'final' / 'chronos2_market_performance.csv')\n"
        "display(mkt_df.head(20))\n"
    ),
    md("## 4. Probabilistic Uncertainty & Prediction Intervals"),
    code(
        "unc_df = pd.read_csv(BASE_DIR / 'outputs' / 'final' / 'chronos2_uncertainty_results.csv')\n"
        "display(unc_df)\n"
    ),
    md("## 5. Conclusions and Production Method Selection\n\n"
       "Analysis of whether the foundation model improves upon persistence or tabular models, followed by justified selection.")
]

with open(NB_DIR / "21_chronos2_experiment.ipynb", "w") as f:
    json.dump({
        "cells": nb21_cells,
        "metadata": {"language_info": {"name": "python"}},
        "nbformat": 4,
        "nbformat_minor": 2
    }, f, indent=2)

print("Generated notebooks/21_chronos2_experiment.ipynb successfully.")
