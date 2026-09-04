# MandiMitra Backend API Reference

Base URL: `http://localhost:8000/api/v1`

## Authentication

### `POST /auth/signup`
Registers a new farmer profile.
- **Request Body**:
  ```json
  {
    "full_name": "Ramesh Patil",
    "mobile": "9876543210",
    "email": "ramesh@example.com",
    "password": "FarmerPassword@2026",
    "state": "Maharashtra",
    "district": "Pune",
    "village": "Manjri",
    "primary_crop": "Wheat",
    "latitude": 18.5204,
    "longitude": 73.8567
  }
  ```
- **Response**: `201 Created` with JWT access token and user payload.

### `POST /auth/login`
Authenticates a user via mobile number or email.
- **Request Body**:
  ```json
  {
    "username": "9876543210",
    "password": "FarmerPassword@2026"
  }
  ```
- **Response**: `200 OK` with JWT access token and user payload.

### `GET /auth/me`
Retrieves current authenticated user profile.
- **Headers**: `Authorization: Bearer <token>`

---

## Mandi Search

### `GET /mandis/nearby`
Finds all registered mandis trading a crop within radius (default: 500 km).
- **Query Parameters**:
  - `crop` (required): `wheat` | `rice` | `tomato` | `cotton`
  - `latitude` (required): float
  - `longitude` (required): float
  - `radius_km` (optional, default: 500.0): float
- **Response**: List of mandis sorted by distance with latest prices.

---

## Price History & Predictions

### `GET /prices/history`
Returns aggregated historical Agmarknet modal prices.
- **Query Parameters**:
  - `crop` (required): `wheat` | `rice` | `tomato` | `cotton`
  - `period` (optional, default: `YTD`): `1D` | `1W` | `3W` | `1M` | `6M` | `YTD`
  - `mandi_id` (optional): string

### `GET /prediction`
Runs ML inference for a specific crop and mandi using the trained models.
- **Query Parameters**:
  - `crop` (required): `wheat` | `rice` | `tomato` | `cotton`
  - `mandi_id` (required): string
  - `variety` (optional, default: `Other`): string
  - `grade` (optional, default: `FAQ`): string
- **Response**: Current modal price, 3-day forecast (`day_1`, `day_2`, `day_3`), and trend (`rising`, `falling`, `stable`).

---

## Recommendation & Decision Support

### `POST /recommendation`
Computes the final selling strategy comparing mandi net payouts, middleman offers, and predicted future prices.
- **Request Body**:
  ```json
  {
    "crop": "wheat",
    "quantity_kg": 1000.0,
    "latitude": 18.5204,
    "longitude": 73.8567,
    "has_middleman": true,
    "middleman_price": 2200.0,
    "middleman_commission": 2.0,
    "middleman_other": 0.0,
    "radius_km": 500.0
  }
  ```
- **Response**:
  ```json
  {
    "recommendation": "SELL TODAY",
    "reason": "Selling today at APMC Pune yields maximum net return of ₹50,627 after ₹873 transport deduction.",
    "crop": "wheat",
    "quantity_kg": 1000.0,
    "quantity_quintals": 10.0,
    "best_mandi": {
      "mandi_id": "maharashtra-pune-apmc-pune",
      "mandi_name": "APMC Pune",
      "distance_km": 87.3,
      "price_per_quintal": 5150.0,
      "transport_cost": 873.0,
      "gross_value": 51500.0,
      "net_value": 50627.0
    },
    "current_net_value": 50627.0,
    "expected_future_price": 4211.77,
    "expected_future_net_value": 41244.7,
    "potential_difference": -9382.3,
    "trend": "falling",
    "weather_advisory": "High rain probability today; use covered transport."
  }
  ```

---

## Weather & Search History

### `GET /weather`
Provides live temperature, weather conditions, precipitation probability, and agro-advisories from Open-Meteo.
- **Query Parameters**:
  - `latitude`: float
  - `longitude`: float
  - `location_name`: string

### `GET /search-history` & `POST /search-history`
Stores and retrieves recent search queries per user in MySQL.
