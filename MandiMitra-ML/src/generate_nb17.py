"""Generate notebook 17 for MandiMitra end-to-end system test."""
import json
from pathlib import Path

BASE_DIR = Path('.').resolve()
NB_DIR = BASE_DIR / "notebooks"
NB_DIR.mkdir(parents=True, exist_ok=True)

def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text}

def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": text}

nb17_cells = [
    md("# Step 17: End-to-End System Test\n\nRun a comprehensive inference test for all 4 crops and edge cases."),
    code(
        "import sys\n"
        "from pathlib import Path\n"
        "import pandas as pd\n"
        "BASE_DIR = Path('..').resolve()\n"
        "if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))\n\n"
        "from src.end_to_end_test import main\n"
        "main()\n"
    ),
    code(
        "df = pd.read_csv(BASE_DIR / 'outputs' / 'final' / 'end_to_end_test_results.csv')\n"
        "display(df)\n"
    )
]

with open(NB_DIR / "17_end_to_end_system_test.ipynb", "w") as f:
    json.dump({"cells": nb17_cells, "metadata": {"language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 2}, f, indent=2)

print("Generated notebook 17.")
