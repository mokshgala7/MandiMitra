import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))

from src.feature_engineering import (
    sort_time_series,
    create_price_lag_features,
    create_rolling_price_features,
    create_price_momentum_features,
    create_price_range_features,
    create_calendar_features
)
from src.predict import predict_mandi_price, EXPECTED_FEATURES as RICE_EXPECTED_FEATURES
from src.multi_crop_predict import predict_price, EXPECTED_FEATURES as MULTI_CROP_EXPECTED_FEATURES

def generate_synthetic_features():
    # User-provided recent prices
    recent_prices = [100, 105, 112, 120, 130, 142, 155, 170, 185, 200, 220, 240, 260, 280, 300]
    
    # Pad with 30 historical values so that 30-day lags and MAs are valid (not NaN)
    # Start at 90 and slowly step to 100
    hist_prices = np.linspace(90, 99, 30).tolist()
    all_prices = hist_prices + recent_prices
    
    n_days = len(all_prices)
    end_date = datetime.now()
    dates = [end_date - timedelta(days=n_days - 1 - i) for i in range(n_days)]
    
    df = pd.DataFrame({
        "Price Date": dates,
        "Market": "Synthetic",
        "Variety": "Test",
        "Grade": "FAQ",
        "Modal Price": all_prices
    })
    
    df["Min Price"] = df["Modal Price"] * 0.95
    df["Max Price"] = df["Modal Price"] * 1.05
    
    # Apply feature engineering
    group_cols = ["Market", "Variety", "Grade"]
    df = sort_time_series(df, group_cols=group_cols, date_col="Price Date")
    df = create_price_lag_features(df, group_cols=group_cols, price_col="Modal Price")
    df = create_rolling_price_features(df, group_cols=group_cols, price_col="Modal Price")
    df = create_price_momentum_features(df, price_col="Modal Price")
    df = create_price_range_features(df)
    df = create_calendar_features(df, date_col="Price Date")
    
    # Get the latest row which has all the historical context
    latest_row = df.iloc[[-1]].copy()
    
    # We will pass this to the prediction functions. The prediction functions expect specific columns
    # which we can verify are present
    return latest_row

def main():
    print("==================================================")
    print("ML VS PERSISTENCE DIAGNOSTIC")
    print("==================================================\n")
    
    synthetic_df = generate_synthetic_features()
    # The latest/current price from the synthetic series
    current_price = synthetic_df["Modal Price"].values[0]
    
    crops = ["Rice", "Tomato", "Wheat", "Cotton"]
    results = []
    
    # Setup output file
    output_dir = base_dir / "outputs" / "final"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_csv = output_dir / "ml_vs_persistence_diagnostic.csv"
    
    all_different = []
    
    for crop in crops:
        print(f"{crop}:")
        
        try:
            # Predict
            sample_dict = synthetic_df.iloc[0].to_dict()
            if crop == "Rice":
                ml_pred = predict_mandi_price(sample_dict)
                model_used = "src/predict.py (Rice Model)"
            else:
                pred_dict = predict_price(crop, sample_dict)
                ml_pred = pred_dict["predicted_price"]
                model_used = f"src/multi_crop_predict.py ({crop} Model)"
                
            persistence_pred = current_price
            
            # The model predicts float; compare with tolerance or strict inequality
            different = abs(ml_pred - persistence_pred) > 1e-4
            diff_str = "YES" if different else "NO"
            
            diff_val = ml_pred - persistence_pred
            
            all_different.append(different)
            
            print(f"ML prediction: ₹{ml_pred:.2f}")
            print(f"Persistence: ₹{persistence_pred:.2f}")
            print(f"Different: {diff_str}\n")
            
            results.append({
                "Crop": crop,
                "Current price": current_price,
                "Persistence prediction": persistence_pred,
                "ML prediction": ml_pred,
                "Difference between ML and persistence": diff_val,
                "ML model used": model_used,
                "PASS/FAIL": "PASS" if different else "FAIL"
            })
            
        except Exception as e:
            print(f"Error predicting for {crop}: {e}\n")
            results.append({
                "Crop": crop,
                "Current price": current_price,
                "Persistence prediction": persistence_pred,
                "ML prediction": np.nan,
                "Difference between ML and persistence": np.nan,
                "ML model used": crop,
                "PASS/FAIL": f"ERROR: {e}"
            })
            
    # Save CSV
    pd.DataFrame(results).to_csv(out_csv, index=False)
    
    print("FINAL DIAGNOSIS:\n")
    if all(all_different) and len(all_different) > 0:
        print("The trained ML models are functioning; production currently")
        print("selects persistence because it performed better during validation.")
    elif not any(all_different) and len(all_different) > 0:
        print("Investigate whether the inference implementation is incorrectly")
        print("routing all predictions through the persistence method.")
    else:
        print("Mixed results. Some models predict persistence exactly, others do not.")
        print("Investigate the specific models predicting persistence.")
        
    print(f"\nResults saved to {out_csv}")

if __name__ == '__main__':
    main()
