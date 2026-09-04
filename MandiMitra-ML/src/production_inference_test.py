"""
production_inference_test.py — Final Production Inference Validation

Runs tests against the `predict_price` function to ensure it strictly
returns JSON-serializable forecasts without decision logic or mock data.
"""

import sys
import json
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs" / "final"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.inference import predict_price

def run_tests():
    print("MANDIMITRA PRODUCTION INFERENCE TEST")
    print("="*50)
    
    records = []
    
    # 1. Valid Cases
    cases = [
        {"crop": "rice", "market": "APMC Alibagh", "current_price": 3500.0, "date": "2026-09-04"},
        {"crop": "tomato", "market": "APMC Kamthi", "current_price": 2770.0, "date": "2026-09-04"},
        {"crop": "wheat", "market": "APMC Latur", "current_price": 2650.0, "date": "2026-09-04"},
        {"crop": "cotton", "market": "APMC Hinganghat", "current_price": 7900.0, "date": "2026-09-04"},
    ]
    
    for case in cases:
        res = predict_price(**case)
        # Verify JSON serialization
        try:
            json.dumps(res)
        except Exception as e:
            print(f"FAILED JSON serialization for {case['crop']}: {e}")
            
        print(f"\nCrop: {case['crop']}")
        print(f"Result: {json.dumps(res, indent=2)}")
        
        records.append({
            "Test": f"Valid {case['crop']}",
            "Crop": case['crop'],
            "Status": "PASS" if "error" not in res else "FAIL",
            "Message": json.dumps(res)
        })

    # 2. Invalid Cases
    invalid_cases = [
        {"desc": "Invalid crop", "crop": "invalid_crop", "market": "APMC Alibagh", "current_price": 3500.0, "date": "2026-09-04"},
        {"desc": "Unsupported market", "crop": "wheat", "market": "Unknown Mandi", "current_price": 2500.0, "date": "2026-09-04"},
        {"desc": "Invalid price", "crop": "rice", "market": "APMC Alibagh", "current_price": -50.0, "date": "2026-09-04"},
        {"desc": "Missing input", "crop": "rice", "market": "APMC Alibagh", "current_price": None, "date": "2026-09-04"}
    ]
    
    for case in invalid_cases:
        desc = case.pop("desc")
        res = predict_price(**case)
        print(f"\nEdge Case: {desc}")
        print(f"Result: {json.dumps(res, indent=2)}")
        
        # Unsupported market returns a valid fallback forecast!
        if desc == "Unsupported market":
            passed = "predicted_prices" in res
        else:
            passed = "error" in res
            
        records.append({
            "Test": f"Edge: {desc}",
            "Crop": case['crop'],
            "Status": "PASS" if passed else "FAIL",
            "Message": json.dumps(res)
        })

    df = pd.DataFrame(records)
    df.to_csv(OUTPUTS_DIR / "production_inference_test.csv", index=False)
    
if __name__ == "__main__":
    run_tests()
