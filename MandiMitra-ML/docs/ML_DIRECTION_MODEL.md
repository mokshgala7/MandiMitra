# MandiMitra ML V3 — Price Direction & Cross-Mandi Intelligence

## 1. Overview & Problem Definition

In agricultural market decision-making, an exact point price forecast (e.g., ₹2,642 vs ₹2,650) is often less important than answering a fundamental strategic question:

> **"Is this mandi's price likely to meaningfully INCREASE, STAY STABLE, or DECREASE over the next ~3 market observations?"**

Because APMC agricultural prices exhibit substantial short-term stickiness, exact regression models often struggle to beat a simple persistence baseline. However, direction classification transforms the forecasting challenge into a high-utility decision support tool:
- **INCREASE**: Suggests holding crop (**WAIT signal**).
- **DECREASE / STABLE**: Suggests liquidating at today's known price (**SELL TODAY signal**).

---

## 2. Empirically Justified Movement Thresholds

To prevent treating economically trivial price fluctuations as genuine trends, movement thresholds were determined strictly from historical training distributions:

| Crop | Volatility Regime | Empirical Threshold | Justification from Training Distribution |
| :--- | :--- | :---: | :--- |
| **Rice** | High Stickiness (68.4% exact zero changes) | **±1.5%** | Separates genuine breakout rallies/drops from stationary periods. |
| **Tomato** | High Perishable Volatility (Mean abs change 19.4%) | **±5.0%** | Distinguishes meaningful market surges from routine daily noise. |
| **Wheat** | Steady Seasonal Trading (Mean abs change 3.0%) | **±1.5%** | Aligns with the 75th percentile of normal 3-observation moves. |
| **Cotton** | Consolidated Seasonal Trading (Mean abs change 1.2%) | **±1.0%** | Captures rare but impactful procurement shifts in a narrow price band. |

---

## 3. Feature Architecture

The direction model leverages three complementary information tiers:

### Tier 1: Historical Series Features
- **Price Anchors**: `Modal Price`, `Min Price`, `Max Price`, `price_range`, `price_range_pct`.
- **Lags & Moving Averages**: `lag_1`, `lag_2`, `lag_3`, `lag_7`, `lag_14`, `lag_30`, `ma_3`, `ma_7`, `ma_14`, `ma_30`.
- **Momentum & Volatility**: Trailing changes (`price_change_1_pct`, `price_change_3_pct`, `price_change_7_pct`), rolling standard deviations (`std_7`, `std_14`, `std_30`).
- **Seasonality & Calendar**: Cyclical sine/cosine encodings of month and day of year.

### Tier 2: Cross-Mandi Intelligence
At every date $T$, spatial statistics are computed across all reporting APMCs for that crop (with zero future leakage):
- `crop_mean_price` & `crop_median_price`: Statewide benchmark prices.
- `crop_price_spread`: Current statewide price dispersion (`max - min`).
- `market_price_minus_crop_mean`: Local mandi premium/discount relative to Maharashtra average.
- `market_price_rank`: Percentile ranking of the mandi's price statewide.
- `crop_pct_markets_increasing`: Percentage of mandis experiencing upward trailing momentum.

### Tier 3: Foundation Model Signals (Chronos-2)
- Zero-shot forecasts from Amazon Chronos-2 (`chronos_pred`, `chronos_pred_pct`).
- Probabilistic prediction interval width (`chronos_p90 - chronos_p10`).

---

## 4. Evaluated Models & Baselines

Models are trained on historical training splits and evaluated on untouched test sets:

1. **Baselines**:
   - **Majority Class**: Predicts the most frequent class in training history.
   - **Persistence (STABLE)**: Always predicts price will remain stable.
   - **Momentum Baseline**: Uses trailing 3-observation price momentum to project forward.
2. **Machine Learning Classifiers**:
   - **Logistic Regression**: Scaled with balanced class weights.
   - **Random Forest Classifier**: Non-linear ensemble with depth constraints and balanced weights.
   - **Gradient Boosting Classifier**: Sequential tree boosting.
   - **HistGradientBoostingClassifier**: High-speed binned gradient boosting.

---

## 5. Decision Relevance & Confidence

Rather than evaluating solely on raw accuracy, models are assessed on decision relevance:
- **Wait Precision**: When the model predicts `INCREASE`, what percentage actually increases?
- **Sell Precision**: When the model predicts `DECREASE` or `STABLE`, what percentage actually does not increase?
- **Calibrated Probabilities**: The model returns class probabilities (`increase`, `stable`, `decrease`), allowing the backend to ignore low-confidence recommendations.

---

## 6. API Interface

The standalone inference interface is exposed in `src/direction_inference.py`:

```python
from src.direction_inference import predict_price_direction

result = predict_price_direction(
    crop="wheat",
    market="APMC Nagpur",
    current_price=2650.0,
    date="2026-09-04"
)
```

Example response:
```json
{
  "crop": "wheat",
  "market": "APMC Nagpur",
  "current_price": 2650.0,
  "predicted_direction": "STABLE",
  "confidence": 0.742,
  "probabilities": {
    "decrease": 0.124,
    "stable": 0.742,
    "increase": 0.134
  },
  "forecast_horizon": "3 market observations",
  "movement_threshold_pct": 1.5,
  "interpretation": "Price is likely to stable by more than 1.5% over ~3 observations with 74.2% confidence.",
  "experimental_method": "direction_v3_classifier"
}
```
