# MandiMitra Final ML/AI System Documentation

## 1. Problem Definition
MandiMitra aims to help farmers decide WHERE and WHEN to sell their crops to maximize returns, by integrating market price forecasting, local market comparisons, and transportation costs into a single decision engine. **This system is a decision-support tool, NOT a guaranteed price predictor.**

## 2. Dataset Sources
Data is sourced from AGMARKNET daily price reports for the state of Maharashtra. It includes Modal Price, Min Price, and Max Price for specific Market, Variety, and Grade combinations.

## 3. Four Crops
The system currently covers four crops:
1. Rice
2. Tomato
3. Wheat
4. Cotton

## 4. Data Cleaning
Raw data is loaded, concatenated, and stripped of extraneous whitespace and formatting. Missing values in crucial columns (like prices) are handled carefully, ensuring data integrity.

## 5. >=500 Threshold
To ensure statistical validity in modeling, only Market + Variety + Grade combinations with at least 500 valid observations in the dataset are retained for Rice, Tomato, and Wheat.

## 6. Cotton >=300 Exception
Cotton data is sparser due to a short seasonal reporting window. No group met the 500-observation threshold, so an adaptive threshold of >=300 was used for Cotton to retain at least one group (APMC Hinganghat | Other | FAQ). Model performance on Cotton should be interpreted cautiously due to this limitation.

## 7. Feature Engineering
Features include:
- Autoregressive price lags (1, 2, 3, 7, 14, 30 days)
- Moving averages and standard deviations (3, 7, 14, 30 days)
- Price changes (absolute and percentage) over recent windows
- Calendar/cyclical features (month sine/cosine, day of year sine/cosine)
- Categorical identifiers (Market, Variety, Grade)

Arrival quantity (supply) was intentionally excluded from the core price models to prevent forecasting dependency on unpredictable future arrivals, though it is supported in the recommendation engine as an external signal.

## 8. Forecast Target
The target is `price_after_3_observations`, which represents the Modal Price approximately 3 trading days in the future for the same Market + Variety + Grade combination.

## 9. Chronological Validation
Data was split chronologically (e.g., first 80% of dates for training, last 20% for testing) to prevent future information leakage into the model.

## 10. Models Tested
- Linear Regression
- Random Forest Regressor
- Gradient Boosting Regressor (or XGBoost if available)
- Persistence Baseline
- Recent Mean (MA-7) Baseline

## 11. Persistence Baseline
The Persistence model assumes that the price after 3 observations will simply be today's price. This provides a strong, robust benchmark in volatile or highly stable commodity markets.

## 12. Why persistence can outperform ML
Many agricultural commodities in APMC markets exhibit strong mean-reversion or short-term price stickiness. Prices may remain flat for long periods or jump unpredictably due to external macro factors not captured by historical price data alone. In these regimes, complex ML models may overfit to noise, making the simple persistence signal the most accurate out-of-sample predictor (e.g., lower MAE).

## 13. Final forecasting-method selection
For each crop, the final forecasting method is selected based on out-of-sample Mean Absolute Error (MAE). If the best ML model does not beat the persistence baseline's MAE by a meaningful margin (e.g., >2%), the system automatically selects `persistence` as the more reliable forecasting method. This ensures robust real-world performance over theoretical complexity.

## 14. Uncertainty Methodology
Forecast uncertainty is estimated empirically using the model's historical validation MAE. A prediction interval is generated around the forecast (±z * MAE), which is widened during periods of detected high market volatility.

## 15. Sell/Wait Logic
The decision to SELL TODAY or WAIT relies on a normalized signal-to-noise ratio: the expected price change (%) divided by the stability threshold (%) derived from historical MAE. A WAIT recommendation is only issued if the expected upside meaningfully exceeds the model's inherent uncertainty and market volatility is not dangerously high. Otherwise, the safer SELL TODAY is recommended.

## 16. Market Comparison
The system compares the home market against nearby markets by computing the **net price** (gross price minus transport cost). If transport cost is unavailable, it ranks based on gross price, but explicitly notes this limitation.

## 17. Transport Interface
The `transport.py` module accepts externally supplied transport costs (per quintal or total) to compute net prices. **It does not fabricate distances or costs.** If not provided, it gracefully degrades to gross-price comparisons.

## 18. Weather Interface
The `weather_features.py` module accepts optional external weather data (temp, rainfall, alerts) to enrich the farmer-facing explanation. The recommendation system functions perfectly without it and never fabricates weather data.

## 19. Supply/Arrival Interface
The `supply_features.py` module accepts optional external supply data (e.g., arrival quantities, surplus/deficit status) to provide context. Like weather, this is never fabricated and the system works without it.

## 20. Limitations
- **Decision-Support Only:** This system supports decisions but cannot foresee unpredictable external shocks (e.g., sudden government policy changes or extreme weather events).
- **Transport Costs:** Requires external real-world inputs to calculate true net profitability.
- **Data Sparsity:** Cotton predictions are based on limited historical observations and must be treated cautiously.

## 21. Backend Integration Schema
The final output is a standardized, strictly-typed JSON response produced by `api_response.py`. Missing data is safely encoded as `null` or `"NOT_AVAILABLE"`, ensuring backend systems will not break or receive hallucinated values.
