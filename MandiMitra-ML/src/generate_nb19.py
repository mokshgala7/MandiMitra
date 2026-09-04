"""Generate notebook 19 for MandiMitra final inference validation."""
import json
from pathlib import Path

BASE_DIR = Path('.').resolve()
NB_DIR = BASE_DIR / "notebooks"
NB_DIR.mkdir(parents=True, exist_ok=True)

def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text}

def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": text}

nb19_cells = [
    md("# Step 19: Production Inference Demo\n\nVerify that the final backend inference interface returns clean JSON forecasts without decision logic."),
    code(
        "import sys\n"
        "from pathlib import Path\n"
        "import pandas as pd\n"
        "BASE_DIR = Path('..').resolve()\n"
        "if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))\n\n"
        "from src.production_inference_test import run_tests\n"
        "run_tests()\n"
    ),
    code(
        "df = pd.read_csv(BASE_DIR / 'outputs' / 'final' / 'production_inference_test.csv')\n"
        "display(df)\n"
    )
]

with open(NB_DIR / "19_production_inference_demo.ipynb", "w") as f:
    json.dump({"cells": nb19_cells, "metadata": {"language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 2}, f, indent=2)

print("Generated notebook 19.")
