# ML Backend Integration Guide

This document contains exact instructions for integrating the MandiMitra ML prediction module into the Flask backend.

## A. Installation

The ML repository should be cloned and installed alongside or as a submodule within the Flask environment.

1. Clone this repository.
2. Install the exact ML dependencies:
```bash
pip install -r requirements.txt
```

## B. Repository Structure

The backend team only needs to interact with `src/inference.py` and ensure that `models/` and `data/processed/` directories are intact when deploying. 

Required for inference:
- `src/inference.py` (The entry point)
- `src/forecast_engine.py` (The internal ML execution engine)
- `models/*.joblib` & `models/*.json` (Trained model weights and metadata)
- `data/processed/maharashtra_*_features.csv` (Historical market contexts)

You can safely ignore or omit notebooks and other raw data in production deployments if space is a concern, but the processed feature CSVs MUST be included.

## C. Exact Import

In your Flask app/service layer, import the prediction function:

```python
from src.inference import predict_price
```

## D. Exact Function Signature

```python
def predict_price(
    crop: str,
    market: str,
    current_price: float,
    date: str
) -> dict:
```
- `crop`: string, must be one of `['rice', 'tomato', 'wheat', 'cotton']`.
- `market`: string, the APMC mandi name (e.g., `"APMC Alibagh"`).
- `current_price`: float, today's Modal Price for the farmer's crop at that mandi (₹/quintal).
- `date`: string, today's date in `YYYY-MM-DD` format.

## E. Exact Return Structure

The function returns a JSON-serializable dictionary. 

**Note on Forecast Horizon**: The ML system predicts a single future price representing the value approximately 3 market observations (trading days) from now. It does not fabricate daily intermediate prices.

```json
{
    "crop": "rice",
    "market": "APMC Alibagh",
    "current_price": 3500.0,
    "forecast_horizon": "1 future value representing price after ~3 market observations",
    "predicted_prices": [3500.0],
    "forecast_method": "persistence",
    "uncertainty": {
        "level": "LOW",
        "lower_bound": 3379.08,
        "upper_bound": 3620.92
    }
}
```

## F. Error Handling

If an unsupported crop is provided, or current_price is invalid (e.g. negative), the function will return a dict containing an `"error"` key.

```json
{
    "error": "Unsupported crop: 'invalid_crop'. Supported: ['rice', 'tomato', 'wheat', 'cotton']"
}
```

The Flask backend should check for the presence of the `"error"` key before using the prediction.

## G. Python Example

```python
from src.inference import predict_price

def get_forecast():
    result = predict_price(
        crop="rice",
        market="APMC Alibagh",
        current_price=3500,
        date="2026-09-04"
    )
    
    if "error" in result:
        print(f"Error occurred: {result['error']}")
        return None
        
    print(f"Predicted Future Price: {result['predicted_prices'][0]}")
    return result
```

## H. How Flask Should Call the Function

The ML module **only provides price forecasts**. The backend is responsible for combining these forecasts with transport costs, distances, and making the final SELL/WAIT decision.

Example Flask Route:

```python
from flask import Flask, request, jsonify
from src.inference import predict_price

app = Flask(__name__)

@app.route("/api/forecast", methods=["POST"])
def forecast_route():
    data = request.json
    
    crop = data.get("crop")
    market = data.get("market")
    current_price = data.get("current_price")
    date = data.get("date")
    
    # 1. Get ML Price Forecast
    ml_result = predict_price(crop, market, current_price, date)
    
    if "error" in ml_result:
        return jsonify(ml_result), 400
        
    # 2. Flask handles external logic (distances, net revenue, SELL/WAIT decision)
    #    e.g. distance = calculate_distance(farmer_loc, mandi_loc)
    #    transport_cost = distance * 15
    #    if ml_result['predicted_prices'][0] > current_price + transport_cost: ...
        
    # Return to frontend
    return jsonify({
        "ml_forecast": ml_result,
        "backend_decision": "WAIT",  # Calculated by Flask, not ML
        "transport_cost_calculated": 450
    })
```
