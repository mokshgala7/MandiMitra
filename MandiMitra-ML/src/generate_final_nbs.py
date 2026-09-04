"""Generate notebooks 14, 15, 16 for MandiMitra ML Final."""
import json
from pathlib import Path
import pandas as pd

BASE_DIR = Path('.').resolve()
NB_DIR = BASE_DIR / "notebooks"
NB_DIR.mkdir(parents=True, exist_ok=True)

def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text}

def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": text}

# ---------------------------------------------------------
# Notebook 14: Final Model Audit
# ---------------------------------------------------------
nb14_cells = [
    md("# Step 14: Final Model Audit\n\nAudit of the existing models to determine the best overall forecasting method for each crop."),
    code(
        "import sys, json\n"
        "from pathlib import Path\n"
        "import pandas as pd\n"
        "BASE_DIR = Path('..').resolve()\n"
        "if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))\n\n"
        "from src.forecast_engine import load_forecast_config, build_forecast_config\n"
        "config = build_forecast_config(save=True)\n"
    ),
    code(
        "CROPS = ['rice', 'tomato', 'wheat', 'cotton']\n"
        "records = []\n"
        "for crop in CROPS:\n"
        "    meta_path = BASE_DIR / 'models' / (f'model_metadata.json' if crop == 'rice' else f'{crop}_model_metadata.json')\n"
        "    with open(meta_path) as f: meta = json.load(f)\n"
        "    rec = {\n"
        "        'Crop': crop.capitalize(),\n"
        "        'Best ML Model': meta.get('model_name', 'Unknown'),\n"
        "        'ML MAE': meta.get('MAE'),\n"
        "        'ML RMSE': meta.get('RMSE'),\n"
        "        'ML MAPE': meta.get('MAPE'),\n"
        "        'ML R2': meta.get('R2'),\n"
        "        'Persistence MAE': meta.get('persistence_baseline_MAE'),\n"
        "        'Persistence RMSE': meta.get('persistence_baseline_RMSE'),\n"
        "        'Persistence MAPE': meta.get('persistence_baseline_MAPE'),\n"
        "        'ML Improvement vs Persistence': meta.get('improvement_vs_persistence_pct'),\n"
        "        'Best ML Method': meta.get('model_name', 'Unknown'),\n"
        "        'Best Overall Method': config[crop]['method']\n"
        "    }\n"
        "    records.append(rec)\n"
        "df = pd.DataFrame(records)\n"
        "(BASE_DIR / 'outputs' / 'final').mkdir(parents=True, exist_ok=True)\n"
        "df.to_csv(BASE_DIR / 'outputs' / 'final' / 'crop_model_summary.csv', index=False)\n"
        "display(df)\n"
        "for crop in CROPS:\n"
        "    print(f\"{crop.capitalize()}: {config[crop]['reason']}\")\n"
    )
]
with open(NB_DIR / "14_final_model_audit.ipynb", "w") as f:
    json.dump({"cells": nb14_cells, "metadata": {"language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 2}, f, indent=2)

# ---------------------------------------------------------
# Notebook 15: Decision Backtest
# ---------------------------------------------------------
nb15_cells = [
    md("# Step 15: Decision Backtest\n\nSimulates historical SELL/WAIT decisions using ONLY information available at that historical prediction point."),
    code(
        "import sys\n"
        "from pathlib import Path\n"
        "import pandas as pd\n"
        "BASE_DIR = Path('..').resolve()\n"
        "if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))\n\n"
        "from src.backtest_decisions import backtest_all_crops\n"
        "results = backtest_all_crops(verbose=True)\n"
    ),
    code(
        "summary = pd.read_csv(BASE_DIR / 'outputs' / 'final' / 'decision_backtest_summary.csv')\n"
        "display(summary)\n"
    )
]
with open(NB_DIR / "15_decision_backtest.ipynb", "w") as f:
    json.dump({"cells": nb15_cells, "metadata": {"language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 2}, f, indent=2)

# ---------------------------------------------------------
# Notebook 16: Final Inference Tests
# ---------------------------------------------------------
nb16_cells = [
    md("# Step 16: Final Inference Tests\n\nTest the recommendation engine for all 4 crops using valid historical examples from the existing datasets."),
    code(
        "import sys, json\n"
        "from pathlib import Path\n"
        "import pandas as pd\n"
        "BASE_DIR = Path('..').resolve()\n"
        "if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))\n\n"
        "from src.mandimitra_recommendation import get_recommendation\n"
    ),
    code(
        "CROPS = ['rice', 'tomato', 'wheat', 'cotton']\n"
        "records = []\n\n"
        "for crop in CROPS:\n"
        "    print(f'\\n{crop.upper()}')\n"
        "    test_path = BASE_DIR / 'data' / 'processed' / (f'maharashtra_{crop}_test.csv')\n"
        "    if not test_path.exists(): continue\n"
        "    df = pd.read_csv(test_path, low_memory=False).dropna(subset=['Modal Price']).head(3)\n"
        "    for _, row in df.iterrows():\n"
        "        features = row.to_dict()\n"
        "        rec = get_recommendation(\n"
        "            crop=crop,\n"
        "            market=row['Market'],\n"
        "            current_price=float(row['Modal Price']),\n"
        "            historical_features=features,\n"
        "            recent_prices=[float(row['Modal Price'])] * 5,  # mock for simplicity\n"
        "            nearby_markets=[\n"
        "                {'market': 'Nearby A', 'current_price': float(row['Modal Price']) + 10, 'transport_cost_per_quintal': 20}\n"
        "            ],\n"
        "            transport_data={'transport_cost_per_quintal': 15},\n"
        "            weather_data={'temperature': 30, 'rainfall_mm': 0},\n"
        "            supply_data={'market_supply_status': 'NORMAL'}\n"
        "        )\n"
        "        print(f\"\\n  Market: {rec['market']} | Price: {rec['current_price']} | Rec: {rec['recommendation']}\")\n"
        "        print(f\"  Reason: {rec['reason']}\")\n"
        "        records.append({\n"
        "            'crop': crop,\n"
        "            'market': rec['market'],\n"
        "            'date': row['Price Date'],\n"
        "            'current_price': rec['current_price'],\n"
        "            'forecast': rec['predicted_price'],\n"
        "            'direction': rec['direction'],\n"
        "            'confidence': rec['confidence'],\n"
        "            'recommendation': rec['recommendation'],\n"
        "            'reason': rec['reason']\n"
        "        })\n"
        "\n"
        "examples_df = pd.DataFrame(records)\n"
        "(BASE_DIR / 'outputs' / 'final').mkdir(parents=True, exist_ok=True)\n"
        "examples_df.to_csv(BASE_DIR / 'outputs' / 'final' / 'market_recommendation_examples.csv', index=False)\n"
    ),
    code(
        "# Validation tests\n"
        "print('\\n--- Validation Tests ---')\n"
        "try:\n"
        "    get_recommendation(crop='invalid_crop', market='X', current_price=100)\n"
        "except ValueError as e:\n"
        "    print('Invalid crop rejected:', e)\n\n"
        "try:\n"
        "    get_recommendation(crop='rice', market='X', current_price=-10)\n"
        "except ValueError as e:\n"
        "    print('Invalid price rejected:', e)\n"
    )
]
with open(NB_DIR / "16_final_inference_tests.ipynb", "w") as f:
    json.dump({"cells": nb16_cells, "metadata": {"language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 2}, f, indent=2)

print("Generated notebooks 14, 15, 16.")
