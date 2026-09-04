# MandiMitra ML Backend Setup & Installation Guide

This guide provides step-by-step instructions for backend engineers to set up and run the MandiMitra ML inference module locally or in a server environment.

---

## 1. Prerequisites

- **Python**: Version `3.10`, `3.11`, `3.12`, or `3.14`.
- **Operating System**: macOS, Linux (Ubuntu/Debian/RHEL), or Windows 10/11.
- **Hardware**: Standard CPU is fully supported (GPU/Apple Silicon MPS acceleration is optional).
- **Disk Space**: ~2 GB (includes PyTorch, transformers, and model artifacts).

---

## 2. Environment Setup

### macOS & Linux:
```bash
# 1. Clone repository and checkout the backend handoff branch
git clone https://github.com/Diyashah08/Mandimitra.git
cd Mandimitra
git checkout moksh-ml-better

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Upgrade pip and install pinned dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Windows (PowerShell):
```powershell
# 1. Clone repository and checkout the backend handoff branch
git clone https://github.com/Diyashah08/Mandimitra.git
cd Mandimitra
git checkout moksh-ml-better

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 4. Upgrade pip and install pinned dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Verify Installation

Run the automated test suite to confirm all models, dependencies, and inference pipelines are working:

```bash
python tests/test_ml_inference.py
```

Expected output:
```text
Running MandiMitra ML Inference Tests...
✓ test_imports passed
✓ test_offline_price_forecast passed (Rice, Tomato, Cotton)
✓ test_chronos_price_forecast passed (Wheat)
✓ test_price_direction_all_crops passed (All 4 crops)
✓ test_invalid_crop passed
✓ test_invalid_price passed
✓ test_invalid_date passed
✓ test_unknown_market_fallback passed

ALL 8 TEST SUITES PASSED CLEANLY!
```

---

## 4. Foundation Model (Chronos-2) Asset Note

- **Model Identifier**: `amazon/chronos-2`
- **First Run Requirement**:
  - Wheat price forecasting uses Amazon Chronos-2.
  - On the first call to `predict_price(crop="wheat", ...)`, `transformers` will download the ~450 MB model weights from Hugging Face and cache them locally in `~/.cache/huggingface/hub/`.
  - Subsequent calls load instantly from the local cache offline.
  - **Rice, Tomato, and Cotton** price forecasts and **all 4 Price Direction** classifiers run **100% offline immediately** using bundled repository model assets (`models/*.joblib`).
