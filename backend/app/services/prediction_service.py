import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Check for ML directory inside project root or adjacent to project root
if (BASE_DIR / "MandiMitra-ML").exists():
    ML_DIR = BASE_DIR / "MandiMitra-ML"
elif (BASE_DIR.parent / "MandiMitra-ML").exists():
    ML_DIR = BASE_DIR.parent / "MandiMitra-ML"
else:
    ML_DIR = BASE_DIR / "MandiMitra-ML"

MODELS_DIR = ML_DIR / "models"

# Check for data directory in frontend/public/data or public/data
if (BASE_DIR / "frontend" / "public" / "data").exists():
    DATA_DIR = BASE_DIR / "frontend" / "public" / "data"
elif (BASE_DIR / "public" / "data").exists():
    DATA_DIR = BASE_DIR / "public" / "data"
else:
    DATA_DIR = BASE_DIR / "public" / "data"

REQUIRED_FEATURES = [
    "Min Price", "Max Price", "Modal Price",
    "price_lag_1", "price_lag_2", "price_lag_3", "price_lag_7", "price_lag_14", "price_lag_30",
    "price_ma_3", "price_ma_7", "price_ma_14", "price_ma_30",
    "price_std_7", "price_std_14", "price_std_30",
    "price_change_1", "price_change_1_pct", "price_change_3", "price_change_3_pct",
    "price_change_7", "price_change_7_pct", "price_change_14", "price_change_14_pct",
    "price_range", "price_range_pct",
    "year", "month", "day", "day_of_week", "day_of_year", "week_of_year", "is_weekend",
    "month_sin", "month_cos", "day_of_year_sin", "day_of_year_cos",
    "Market", "Variety", "Grade"
]


def _date_sortable(date_str: str) -> int:
    """Convert DD-MM-YYYY to YYYYMMDD int for sorting. Avoids pd.to_datetime."""
    try:
        parts = str(date_str).strip().split("-")
        return int(parts[2]) * 10000 + int(parts[1]) * 100 + int(parts[0])
    except Exception:
        return 0


def _extract_date_fields_vectorised(date_series: pd.Series) -> pd.DataFrame:
    """
    Extract year, month, day, day_of_week, day_of_year, week_of_year, is_weekend
    from a string Series in DD-MM-YYYY format using numpy and pure Python.
    Avoids pd.to_datetime which hangs on Python 3.14 with large Series.
    """
    import calendar
    from datetime import date as dt_date

    records = []
    for raw in date_series:
        try:
            parts = str(raw).strip().split("-")
            day_v   = int(parts[0])
            month_v = int(parts[1])
            year_v  = int(parts[2])
            d = dt_date(year_v, month_v, day_v)
            # day_of_year
            doy = d.timetuple().tm_yday
            # iso week
            iso = d.isocalendar()
            records.append({
                "year": year_v,
                "month": month_v,
                "day": day_v,
                "day_of_week": d.weekday(),       # 0=Mon, 6=Sun
                "day_of_year": doy,
                "week_of_year": iso[1],
                "is_weekend": int(d.weekday() >= 5)
            })
        except Exception:
            records.append({
                "year": None, "month": None, "day": None,
                "day_of_week": None, "day_of_year": None,
                "week_of_year": None, "is_weekend": 0
            })
    return pd.DataFrame(records, index=date_series.index)


class PredictionService:
    def __init__(self):
        self.models = {}
        self.metadata = {}

    def load_metadata(self, crop: str) -> Dict[str, Any]:
        crop_clean = crop.lower()
        if crop_clean not in self.metadata:
            meta_paths = {
                "rice": MODELS_DIR / "model_metadata.json",
                "tomato": MODELS_DIR / "tomato_model_metadata.json",
                "wheat": MODELS_DIR / "wheat_model_metadata.json",
                "cotton": MODELS_DIR / "cotton_model_metadata.json",
            }
            path = meta_paths.get(crop_clean)
            if path and path.exists():
                import json
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self.metadata[crop_clean] = json.load(f)
                except Exception:
                    self.metadata[crop_clean] = {}
            else:
                self.metadata[crop_clean] = {}
        return self.metadata[crop_clean]

    def load_model(self, crop: str):
        if crop not in self.models:
            model_path = MODELS_DIR / f"mandimitra_{crop}_price_model.joblib"
            if not model_path.exists():
                raise FileNotFoundError(f"Model for {crop} not found at {model_path}")
            self.models[crop] = joblib.load(model_path)
        return self.models[crop]

    def engineer_features_for_inference(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Recreates exactly the multi_crop_feature_engineering.py logic.
        df must already be filtered to Market/Variety/Grade and sorted chronologically.
        """
        out = df.copy()

        # --- Numeric prices ---
        for col in ["Modal Price", "Min Price", "Max Price"]:
            out[col] = pd.to_numeric(out[col].astype(str).str.replace(",", ""), errors="coerce")

        price = out["Modal Price"].copy()

        # --- Lags (observation-based, exactly as in training) ---
        out["price_lag_1"]  = price.shift(1)
        out["price_lag_2"]  = price.shift(2)
        out["price_lag_3"]  = price.shift(3)
        out["price_lag_7"]  = price.shift(7)
        out["price_lag_14"] = price.shift(14)
        out["price_lag_30"] = price.shift(30)

        # --- Rolling means ---
        p1 = price.shift(1)
        out["price_ma_3"]  = p1.rolling(window=3,  min_periods=3).mean()
        out["price_ma_7"]  = p1.rolling(window=7,  min_periods=7).mean()
        out["price_ma_14"] = p1.rolling(window=14, min_periods=14).mean()
        out["price_ma_30"] = p1.rolling(window=30, min_periods=30).mean()

        # --- Rolling stds ---
        out["price_std_7"]  = p1.rolling(window=7,  min_periods=7).std()
        out["price_std_14"] = p1.rolling(window=14, min_periods=14).std()
        out["price_std_30"] = p1.rolling(window=30, min_periods=30).std()

        # --- Momentum ---
        out["price_change_1"]     = price - price.shift(1)
        out["price_change_1_pct"] = out["price_change_1"] / price.shift(1)
        out["price_change_3"]     = price - price.shift(3)
        out["price_change_3_pct"] = out["price_change_3"] / price.shift(3)
        out["price_change_7"]     = price - price.shift(7)
        out["price_change_7_pct"] = out["price_change_7"] / price.shift(7)
        out["price_change_14"]    = price - price.shift(14)
        out["price_change_14_pct"]= out["price_change_14"] / price.shift(14)

        # --- Spread ---
        out["price_range"]     = out["Max Price"] - out["Min Price"]
        out["price_range_pct"] = out["price_range"] / out["Modal Price"]

        # --- Calendar features (no pd.to_datetime — avoids Py3.14 hang) ---
        date_df = _extract_date_fields_vectorised(out["Price Date"])
        out = pd.concat([out.reset_index(drop=True), date_df.reset_index(drop=True)], axis=1)

        # Cyclical encoding
        m_vals = out["month"].to_numpy(dtype=float)
        doy_vals = out["day_of_year"].to_numpy(dtype=float)
        out["month_sin"]        = np.sin(2.0 * np.pi * m_vals / 12.0)
        out["month_cos"]        = np.cos(2.0 * np.pi * m_vals / 12.0)
        out["day_of_year_sin"]  = np.sin(2.0 * np.pi * doy_vals / 365.25)
        out["day_of_year_cos"]  = np.cos(2.0 * np.pi * doy_vals / 365.25)

        return out

    def predict(self, crop: str, market: str, variety: str = "Other", grade: str = "FAQ") -> Dict[str, Any]:
        # 1. Load CSV
        csv_path = DATA_DIR / f"{crop}.csv"
        if not csv_path.exists():
            raise ValueError(f"Data for crop '{crop}' not found.")

        df = pd.read_csv(csv_path, skiprows=1, encoding="utf-8")
        df.columns = [c.strip() for c in df.columns]

        # 2. Filter to Market
        market_df = df[df["Market"].str.strip() == market].copy()
        if market_df.empty:
            raise ValueError(f"No price history found for mandi '{market}' in {crop} dataset.")

        # Match exact group or find best available variety/grade for this market
        group_df = market_df[
            (market_df["Variety"].str.strip() == variety) &
            (market_df["Grade"].str.strip() == grade)
        ].copy()

        if len(group_df) < 31:
            # Fallback to the largest group for this market
            group_counts = market_df.groupby(["Variety", "Grade"]).size().reset_index(name="count")
            if not group_counts.empty:
                best_grp = group_counts.sort_values("count", ascending=False).iloc[0]
                best_variety = str(best_grp["Variety"]).strip()
                best_grade = str(best_grp["Grade"]).strip()
                group_df = market_df[
                    (market_df["Variety"].str.strip() == best_variety) &
                    (market_df["Grade"].str.strip() == best_grade)
                ].copy()
                variety = best_variety
                grade = best_grade

        if len(group_df) == 0:
             raise ValueError(f"No historical prices available for {market}.")

        # 3. Sort chronologically
        group_df["_date_sort"] = group_df["Price Date"].apply(_date_sortable)
        group_df = group_df.sort_values("_date_sort").reset_index(drop=True)
        
        # 4. Handle Insufficient Data
        insufficient_data = len(group_df) < 31
        notice = None

        if insufficient_data:
            latest_row = group_df.iloc[-1:]
            current_price_str = str(latest_row["Modal Price"].values[0]).replace(",", "")
            current_price = float(pd.to_numeric(current_price_str, errors="coerce"))
            if pd.isna(current_price):
                current_price = 0.0
            notice = f"Limited historical data — ML unavailable for this mandi/variety. Found {len(group_df)} rows, need 31."
            method_used = "Persistence Baseline"
            predicted_day_3 = current_price
            prediction_date_str = str(latest_row["Price Date"].values[0]).strip()
        else:
            # 5. Engineer features
            features_df = self.engineer_features_for_inference(group_df)
            latest_row = features_df.iloc[-1:]
            current_price = float(latest_row["Modal Price"].values[0])
            prediction_date_str = str(latest_row["Price Date"].values[0]).strip()
            
            # 6. Build feature matrix
            X_infer = latest_row[REQUIRED_FEATURES].copy()

            # 7. Determine configured forecast method
            meta = self.load_metadata(crop)
            trained_markets = [m.strip().lower() for m in meta.get("markets", [])]
            is_trained_market = market.strip().lower() in trained_markets

            config_file = MODELS_DIR / "forecast_method_config.json"
            config_method = "ml" # default if not specified
            if config_file.exists():
                import json
                try:
                    with open(config_file) as f:
                        cfg = json.load(f)
                        config_method = cfg.get(crop.lower(), {}).get("method", "ml").lower()
                except Exception:
                    pass
            
            # Determine method_used logically
            if config_method == "persistence":
                method_used = "Persistence Baseline"
            elif config_method == "chronos-2":
                method_used = "Chronos-2 Baseline"
            elif config_method == "sma":
                method_used = "Recent Mean / SMA"
            elif config_method == "ema":
                method_used = "EMA"
            elif not is_trained_market:
                method_used = "Baseline Fallback"
            else:
                method_used = "Gradient Boosting / ML"

            # 8. Run Prediction / Fallback Logic
            if method_used == "Gradient Boosting / ML":
                try:
                    model = self.load_model(crop)
                    raw_pred = float(model.predict(X_infer)[0])
                    max_allowed = current_price * 1.02
                    min_allowed = current_price * 0.98
                    if raw_pred > max_allowed or raw_pred < min_allowed:
                        # REJECT: Outside validated range. Fallback to Persistence.
                        method_used = "Persistence Baseline"
                        predicted_day_3 = current_price
                        notice = "ML prediction rejected — outside validated range"
                    else:
                        predicted_day_3 = round(raw_pred, 2)
                except Exception as e:
                    method_used = "Persistence Baseline"
                    predicted_day_3 = current_price
                    notice = "ML inference failed — using fallback"
            else:
                # Baseline calculation for non-ML methods (apply slight momentum if possible)
                p_change = 0.0
                if "price_change_3_pct" in latest_row.columns:
                    raw_pct = latest_row["price_change_3_pct"].values[0]
                    if pd.notna(raw_pct):
                        p_change = float(raw_pct)
                        p_change = max(-0.015, min(0.015, p_change))
                predicted_day_3 = round(current_price * (1.0 + p_change), 2)

        # 9. Interpolate Day 1 and Day 2
        diff  = predicted_day_3 - current_price
        day_1 = current_price + diff * (1 / 3)
        day_2 = current_price + diff * (2 / 3)

        # 10. Trend derivation based on FINAL validated forecast
        trend = "stable"
        if predicted_day_3 > current_price * 1.01:
            trend = "rising"
        elif predicted_day_3 < current_price * 0.99:
            trend = "falling"

        forecast_obj = {
            "day_1": round(day_1, 2),
            "day_2": round(day_2, 2),
            "day_3": round(predicted_day_3, 2)
        }

        resp = {
            "crop": crop,
            "mandi_id": "",
            "market": market,
            "variety": variety,
            "grade": grade,
            "current_price": round(current_price, 2),
            "forecast": forecast_obj,
            "predictions": forecast_obj,
            "trend": trend,
            "prediction_date": prediction_date_str,
            "forecast_method": method_used
        }
        if notice:
            resp["notice"] = notice
            
        return resp