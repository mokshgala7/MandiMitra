# MandiMitra — Backend ML Integration Guide

This document defines the interface between the **Flask Backend** and the **MandiMitra Machine Learning Module**.

---

## 1. Architectural Separation of Responsibilities

To ensure modularity and clean engineering:

### The ML Module is strictly responsible for:
1. **Price Forecasting**: Predicting the future price approximately 3 market observations ahead.
2. **Forecast Uncertainty**: Returning empirical error bounds (`lower_bound`, `upper_bound`).
3. **Price Direction**: Predicting categorical trend (`INCREASE`, `STABLE`, `DECREASE`) with calibrated class probabilities.

### The Flask Backend is responsible for:
1. Farmer location, latitude/longitude, and search radius (500 km).
2. Farmer crop quantity (in quintals).
3. Distance calculation between the farmer and candidate APMCs.
4. Transport logistics: ₹15/km transportation cost and net revenue calculation (`Net Revenue = (Price * Quantity) - (Distance * 15 * 2)`).
5. External factors: weather, perishable spoilage risk, storage constraints.
6. Final **SELL TODAY vs. WAIT** decision and UI formatting.

---

## 2. API 1: Price Forecasting

### Import
```python
from src.inference import predict_price
```

### Signature
```python
def predict_price(
    crop: str,
    market: str,
    current_price: float,
    date: str
) -> dict
```

### Parameters
| Parameter | Type | Example | Description |
| :--- | :--- | :--- | :--- |
| `crop` | `str` | `"wheat"`, `"rice"`, `"tomato"`, `"cotton"` | Case-insensitive crop name. |
| `market` | `str` | `"APMC Nagpur"` | Standardized APMC mandi name. |
| `current_price` | `float` | `2650.0` | Today's Modal Price in ₹/quintal (must be > 0). |
| `date` | `str` | `"2025-05-15"` | Current date in `YYYY-MM-DD` format. |

### Crop-Specific Production Model Routing
| Crop | Production Method | Rationale |
| :--- | :--- | :--- |
| **Wheat** | **Amazon Chronos-2** | Zero-shot foundation model achieved ₹62.75 MAE (beating persistence by +7.1%). |
| **Rice** | **Persistence** | Stationary price regime (68% zero moves); persistence achieved ₹120.92 MAE. |
| **Tomato** | **Persistence** | Lightweight baseline (₹409.59 MAE), matching Chronos-2 without model overhead. |
| **Cotton** | **Persistence** | Highly consolidated seasonal prices; persistence achieved ₹103.62 MAE. |

### Successful Response Format
```json
{
  "crop": "wheat",
  "market": "APMC Nagpur",
  "current_price": 2650.0,
  "predicted_price": 3423.28,
  "predicted_prices": [3423.28],
  "forecast_method": "chronos-2",
  "forecast_horizon": "3 market observations",
  "uncertainty": {
    "level": "LOW",
    "lower_bound": 3403.09,
    "upper_bound": 3424.88
  }
}
```

### Error Response Format
If validation fails:
```json
{
  "error": "Unsupported crop: 'mango'. Supported: ['rice', 'tomato', 'wheat', 'cotton']"
}
```

---

## 3. API 2: Price Direction Prediction

### Import
```python
from src.direction_inference import predict_price_direction
```

### Signature
```python
def predict_price_direction(
    crop: str,
    market: str,
    current_price: float,
    date: str
) -> dict
```

### Parameters
Matches `predict_price` (`crop`, `market`, `current_price`, `date`).

### Crop-Specific Direction Model Routing & Thresholds
| Crop | Model Architecture | Movement Threshold | Justification |
| :--- | :--- | :---: | :--- |
| **Wheat** | Random Forest Classifier | **±1.5%** | Separates seasonal trends from daily noise (87.6% SELL precision). |
| **Tomato** | Random Forest Classifier | **±5.0%** | Distinguishes perishable market rallies from volatility (86.2% SELL precision). |
| **Rice** | Gradient Boosting Classifier | **±1.5%** | Separates breakouts from 68% sticky trading days. |
| **Cotton** | Gradient Boosting Classifier | **±1.0%** | Detects shifts in narrow price range (71.4% WAIT precision, 80.8% SELL precision). |

### Successful Response Format
```json
{
  "crop": "wheat",
  "market": "APMC Nagpur",
  "current_price": 2650.0,
  "predicted_direction": "STABLE",
  "confidence": 0.491,
  "probabilities": {
    "decrease": 0.243,
    "stable": 0.491,
    "increase": 0.266
  },
  "forecast_horizon": "3 market observations",
  "movement_threshold_pct": 1.5,
  "interpretation": "Price is expected to stable by more than 1.5% over ~3 observations with 49.1% model confidence.",
  "status": "SUCCESS"
}
```

---

## 4. Example Integration in Flask

```python
from flask import Flask, request, jsonify
from src.inference import predict_price
from src.direction_inference import predict_price_direction

app = Flask(__name__)

@app.route("/api/forecast", methods=["POST"])
def get_mandi_forecast():
    data = request.get_json() or {}
    crop = data.get("crop")
    market = data.get("market")
    current_price = data.get("current_price")
    date = data.get("date")

    # 1. Price Forecast
    forecast = predict_price(crop, market, current_price, date)
    if "error" in forecast:
        return jsonify(forecast), 400

    # 2. Price Direction
    direction = predict_price_direction(crop, market, current_price, date)

    # 3. Combine for Flask response
    response_payload = {
        "price_forecast": forecast,
        "direction_intelligence": direction
    }
    return jsonify(response_payload), 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)
```

---

## 5. Model Assets & Dependencies

All model assets are stored with repository-relative paths inside the `models/` directory:
- `models/direction_model_wheat.joblib`
- `models/direction_model_tomato.joblib`
- `models/direction_model_rice.joblib`
- `models/direction_model_cotton.joblib`
- `models/direction_config.json`
- `models/forecast_method_config.json`

Runtime feature lookup files are stored in `data/processed/maharashtra_*_features.csv`.
No hardcoded paths or environment variables are required.
