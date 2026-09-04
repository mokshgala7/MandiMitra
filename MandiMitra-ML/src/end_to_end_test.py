"""
end_to_end_test.py — Comprehensive MandiMitra ML/AI System Test

Tests the full recommendation pipeline end-to-end across all 4 crops
and verifies edge cases without modifying any data or models.
"""

import sys
import json
import traceback
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUTS_DIR = BASE_DIR / "outputs" / "final"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.mandimitra_recommendation import get_recommendation

CROPS = ["rice", "tomato", "wheat", "cotton"]

test_results = []
summary = {
    "Total tests": 0,
    "Passed": 0,
    "Failed": 0,
    "Warnings": 0,
    "Failures by component": {
        "Data loading": 0,
        "Feature engineering": 0,
        "Forecasting": 0,
        "Direction": 0,
        "Uncertainty": 0,
        "Market comparison": 0,
        "Transport": 0,
        "Weather": 0,
        "Supply": 0,
        "Decision engine": 0,
        "Explanation": 0,
        "API response": 0,
    }
}

def run_test(case_name, crop, market, current_price, features=None, recent_prices=None,
             nearby_markets=None, transport_data=None, weather_data=None, supply_data=None,
             actual_future_price=None, expect_error=False):
    global summary
    summary["Total tests"] += 1
    
    passed = False
    fail_reason = ""
    error_component = ""
    api_response = {}
    
    try:
        # Run recommendation
        api_response = get_recommendation(
            crop=crop,
            market=market,
            current_price=current_price,
            historical_features=features,
            recent_prices=recent_prices,
            nearby_markets=nearby_markets,
            transport_data=transport_data,
            weather_data=weather_data,
            supply_data=supply_data
        )
        
        # Validations if no error is expected
        if expect_error:
            passed = False
            fail_reason = "Expected error but function succeeded."
            error_component = "API response"
        else:
            # Check structure
            for k in ["crop", "market", "current_price", "forecast_method", "predicted_price", 
                      "direction", "confidence", "recommendation", "reason"]:
                if k not in api_response:
                    raise KeyError(f"Missing key in API response: {k}")
            
            # Numeric price checks
            if not isinstance(api_response["predicted_price"], (int, float)):
                raise ValueError(f"Forecast price is not numeric: {api_response['predicted_price']}")
            if api_response["predicted_price"] < 0:
                raise ValueError("Negative forecast price.")
            if current_price < 0:
                raise ValueError("Negative current price.")
                
            # Decision checks
            if api_response["recommendation"] not in ["SELL TODAY", "WAIT"]:
                raise ValueError(f"Invalid recommendation: {api_response['recommendation']}")
                
            if len(api_response["reason"]) < 10:
                raise ValueError("Explanation seems too short or hallucinated.")
                
            # NaNs check
            for k, v in api_response.items():
                if isinstance(v, list): continue
                if pd.isna(v) and v is not None and v != "NOT_AVAILABLE":
                    if isinstance(v, float) and np.isnan(v):
                        raise ValueError(f"NaN leaked into API response at {k}")
            
            passed = True
            
    except Exception as e:
        if expect_error:
            passed = True
            api_response["reason"] = f"Caught expected error: {str(e)}"
        else:
            passed = False
            fail_reason = str(e)
            tb = traceback.format_exc()
            if "forecast" in tb.lower() or "model" in tb.lower(): error_component = "Forecasting"
            elif "direction" in tb.lower(): error_component = "Direction"
            elif "decision" in tb.lower() or "recommendation" in tb.lower(): error_component = "Decision engine"
            elif "transport" in tb.lower(): error_component = "Transport"
            elif "weather" in tb.lower(): error_component = "Weather"
            elif "supply" in tb.lower(): error_component = "Supply"
            elif "explanation" in tb.lower(): error_component = "Explanation"
            elif "market_comparison" in tb.lower(): error_component = "Market comparison"
            elif "uncertainty" in tb.lower(): error_component = "Uncertainty"
            else: error_component = "API response"
            
    if passed:
        summary["Passed"] += 1
    else:
        summary["Failed"] += 1
        if error_component:
            summary["Failures by component"][error_component] += 1
            
    if "data_warnings" in api_response and api_response["data_warnings"]:
        summary["Warnings"] += len(api_response["data_warnings"])
        
    actual = actual_future_price if actual_future_price is not None else "N/A"
    err = (api_response.get("predicted_price", 0) - actual) if isinstance(actual, (int, float)) and "predicted_price" in api_response else "N/A"
    
    print(f"\n{'='*50}")
    print(f"Test Case: {case_name}")
    print(f"Crop: {crop}")
    print(f"Market: {market}")
    print(f"Current Price: {current_price}")
    print(f"Forecast Method: {api_response.get('forecast_method', 'N/A')}")
    print(f"Forecast Price: {api_response.get('predicted_price', 'N/A')}")
    print(f"Expected/Actual Future Price: {actual}")
    print(f"Forecast Error: {err}")
    print(f"Direction: {api_response.get('direction', 'N/A')}")
    print(f"Uncertainty: {api_response.get('confidence', 'N/A')} (Band: {api_response.get('forecast_lower_bound')} to {api_response.get('forecast_upper_bound')})")
    print(f"Best Alternative Market: {api_response.get('best_market', 'N/A')}")
    print(f"Current Net Price: {api_response.get('transport_cost', 'N/A')} TC -> Net N/A (home_net implicitly handled if no tc diff)")
    print(f"Alternative Net Price: {api_response.get('best_market_net_price', 'N/A')}")
    print(f"Recommendation: {api_response.get('recommendation', 'N/A')}")
    print(f"Explanation: {api_response.get('reason', 'N/A')}")
    if not passed:
        print(f"FAIL REASON: {fail_reason}")
    print(f"PASS/FAIL: {'PASS' if passed else 'FAIL'}")
    
    test_results.append({
        "Case": case_name,
        "Crop": crop,
        "Market": market,
        "Current Price": current_price,
        "Forecast Method": api_response.get('forecast_method', 'N/A'),
        "Predicted Price": api_response.get('predicted_price', 'N/A'),
        "Recommendation": api_response.get('recommendation', 'N/A'),
        "Pass/Fail": "PASS" if passed else "FAIL",
        "Error Reason": fail_reason if not passed else ""
    })

def main():
    print("MANDIMITRA END-TO-END SYSTEM TEST")
    
    # 1. Normal historical test cases (3 per crop)
    for crop in CROPS:
        test_path = PROCESSED_DIR / f"maharashtra_{crop}_test.csv"
        if not test_path.exists():
            print(f"Missing {test_path}")
            continue
            
        df = pd.read_csv(test_path, low_memory=False).dropna(subset=['Modal Price', 'price_after_3_observations'])
        if len(df) == 0:
            continue
            
        # Select 3 rows: first, middle, last
        idx_list = [0, len(df)//2, len(df)-1]
        for i, idx in enumerate(idx_list):
            row = df.iloc[idx]
            features = row.to_dict()
            recent_prices = []
            for lag in ["price_lag_30", "price_lag_14", "price_lag_7", "price_lag_3", "price_lag_2", "price_lag_1"]:
                if lag in features and not pd.isna(features[lag]):
                    recent_prices.append(float(features[lag]))
            recent_prices.append(float(row['Modal Price']))
            
            run_test(
                case_name=f"{crop.capitalize()} Valid Case {i+1}",
                crop=crop,
                market=row['Market'],
                current_price=float(row['Modal Price']),
                features=features,
                recent_prices=recent_prices,
                nearby_markets=[
                    {"market": "Nearby A", "current_price": float(row['Modal Price']) + 50, "transport_cost_per_quintal": 20},
                    {"market": "Nearby B", "current_price": float(row['Modal Price']) - 10, "transport_cost_per_quintal": 5}
                ],
                transport_data={"transport_cost_per_quintal": 0}, # Home transport cost
                actual_future_price=float(row['price_after_3_observations'])
            )
            
    # 2. Edge Cases
    # Unknown Crop
    run_test("Edge Case: Unknown Crop", "invalid_crop", "Some Market", 1000, expect_error=True)
    
    # Unknown Market (Should still work, just no historical context means fallback to persistence)
    run_test("Edge Case: Unknown Market", "wheat", "Unknown APMC", 2500, expect_error=False)
    
    # Missing optional weather data (already tested above, but explicitly here)
    run_test("Edge Case: Missing Optional Data (Weather/Transport/Supply)", "tomato", "APMC Pune", 3000, weather_data=None, transport_data=None, supply_data=None, expect_error=False)
    
    # Insufficient historical observations
    run_test("Edge Case: Insufficient historical observations", "rice", "APMC Alibagh", 3500, recent_prices=[], expect_error=False)
    
    # Latest available date
    # Let's get the max date for cotton as the limited data case
    df_cot = pd.read_csv(PROCESSED_DIR / "maharashtra_cotton_test.csv", low_memory=False).dropna(subset=['Modal Price'])
    if len(df_cot) > 0:
        row_max = df_cot.sort_values("Price Date").iloc[-1]
        features_c = row_max.to_dict()
        run_test("Edge Case: Latest Available Date (Cotton)", "cotton", row_max['Market'], float(row_max['Modal Price']), features=features_c, expect_error=False)

    print(f"\n{'='*50}")
    print("FINAL TEST REPORT")
    print(f"{'='*50}")
    print(f"Total tests: {summary['Total tests']}")
    print(f"Passed: {summary['Passed']}")
    print(f"Failed: {summary['Failed']}")
    print(f"Warnings: {summary['Warnings']}")
    
    if summary['Failed'] > 0:
        print("\nBreak failures down by:")
        for k, v in summary['Failures by component'].items():
            if v > 0:
                print(f"- {k}: {v}")
                
    verdict = "SYSTEM READY" if summary['Failed'] == 0 and summary['Warnings'] == 0 else ("READY WITH WARNINGS" if summary['Failed'] == 0 else "NOT READY")
    print(f"\nVerdict: {verdict}")
    
    pd.DataFrame(test_results).to_csv(OUTPUTS_DIR / "end_to_end_test_results.csv", index=False)
    
if __name__ == "__main__":
    main()
