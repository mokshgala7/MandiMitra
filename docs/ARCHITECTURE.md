# MandiMitra System Architecture

## Overview
MandiMitra is a crop-selling decision-support platform designed for Indian farmers. It integrates a React frontend, Python FastAPI backend, MySQL database, and machine learning price prediction models.

## Architectural Layers

```
+-------------------------------------------------------------+
|                      React/Vite Frontend                    |
|       Farmer UI • Geolocation • Charts • Recommendation     |
+-------------------------------------------------------------+
                              |
                              | HTTP / JSON REST
                              v
+-------------------------------------------------------------+
|                     FastAPI Backend Layer                   |
|   Auth (JWT) • Mandi Search (500km) • Decision Engine       |
+-------------------------------------------------------------+
         /                    |                    \
        /                     |                     \
       v                      v                      v
+-------------+      +-------------------+      +-------------------+
|    MySQL    |      |  MandiMitra-ML    |      |  Open-Meteo API   |
|  Database   |      |  GradientBoosting |      |  Live Weather     |
| 283 Mandis  |      |  40 Features/Crop |      |  Rain Advisory    |
+-------------+      +-------------------+      +-------------------+
```

### 1. Frontend Layer (`frontend/`)
- Built with React and Vite.
- Responsive, farmer-first design with simple controls and large text.
- Step-by-step workflow:
  1. Crop Selection (Wheat, Rice, Tomato, Cotton).
  2. Harvest weight in Kilograms (auto-converted to Quintals: 1 Quintal = 100 KG).
  3. Middleman comparison toggle (offer price, commission %, deductions).
  4. Farm location capture via GPS or manual selection.
  5. 500 KM radius mandi discovery with flat ₹10/km transport deduction.
  6. Dynamic `⭐ BEST OPTION` badge on the mandi with highest net payout.
  7. Historical price chart (Recharts) and 2–3 day ML price forecast.
  8. Algorithmic `SELL TODAY` vs `HOLD FOR 2–3 DAYS` recommendation.
  9. Live agro-weather widget.

### 2. Backend Layer (`backend/`)
- Framework: FastAPI (Python 3.10+ / 3.14 compatible).
- Security: Password hashing with Argon2id; stateless JWT bearer authentication.
- Distance Calculation: Haversine spherical distance formula for all mandis within 500 km.
- Recommendation Engine:
  - Current Best Net Value = $\max(Price \times Quintals - Distance \times 10)$.
  - Middleman Net Payout = $(Offer \times Quintals) - Commission - Deductions$.
  - Predicted Future Net Value = $(Forecast \times Quintals) - Distance \times 10$.
  - Threshold rule: Suggests `HOLD FOR 2–3 DAYS` only if predicted net exceeds best current option by $> 2\%$ and trend is rising; otherwise recommends `SELL TODAY`.

### 3. ML Layer (`MandiMitra-ML/`)
- Pre-trained scikit-learn models (`mandimitra_{crop}_price_model.joblib`).
- Zero future data leakage.
- 40 exact temporal, lag, rolling, and categorical features.
- Direction classifiers providing price momentum analysis.

### 4. Database Layer (`backend/schema.sql`)
- Engine: MySQL 8.0+.
- Tables:
  - `users`: Farmer profiles, mobile number, coordinates, primary crop.
  - `mandis`: 283 mandis with verified latitudes/longitudes.
  - `crop_prices`: 31,270 Agmarknet modal, min, max price records.
  - `search_history`: Search queries and parameters per user.
