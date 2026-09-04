"""Generate notebook 18 for MandiMitra final decision engine validation."""
import json
from pathlib import Path

BASE_DIR = Path('.').resolve()
NB_DIR = BASE_DIR / "notebooks"
NB_DIR.mkdir(parents=True, exist_ok=True)

def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text}

def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": text}

nb18_cells = [
    md("# Step 18: Decision Engine Validation\n\nVerify that the recommendation engine produces logically different outcomes for diverse scenarios and handles edge-cases robustly."),
    code(
        "import sys\n"
        "from pathlib import Path\n"
        "import pandas as pd\n"
        "BASE_DIR = Path('..').resolve()\n"
        "if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))\n\n"
        "from src.decision_engine_validation import run_validation\n"
        "run_validation()\n"
    ),
    code(
        "df = pd.read_csv(BASE_DIR / 'outputs' / 'final' / 'decision_engine_validation.csv')\n"
        "display(df)\n"
    )
]

with open(NB_DIR / "18_decision_engine_validation.ipynb", "w") as f:
    json.dump({"cells": nb18_cells, "metadata": {"language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 2}, f, indent=2)

print("Generated notebook 18.")
