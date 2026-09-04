"""
tests/test_ml_inference.py — Real reproducible tests for MandiMitra ML inference.

Tests both:
1. Price Forecasting (`src.inference.predict_price`)
2. Price Direction (`src.direction_inference.predict_price_direction`)
"""

import sys
import json
from pathlib import Path

# Ensure repository root is in python path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.inference import predict_price
from src.direction_inference import predict_price_direction

# Verified real markets from repository data
REAL_TEST_CASES = {
    "wheat": {
        "crop": "wheat",
        "market": "APMC Nagpur",
        "current_price": 2650.0,
        "date": "2025-05-15"
    },
    "rice": {
        "crop": "rice",
        "market": "APMC Alibagh",
        "current_price": 3500.0,
        "date": "2025-05-15"
    },
    "tomato": {
        "crop": "tomato",
        "market": "APMC Kamthi",
        "current_price": 2770.0,
        "date": "2025-05-15"
    },
    "cotton": {
        "crop": "cotton",
        "market": "APMC Hinganghat",
        "current_price": 7900.0,
        "date": "2025-05-15"
    }
}


def test_imports():
    """Verify that both public inference interfaces import successfully."""
    from src.inference import predict_price
    from src.direction_inference import predict_price_direction
    assert callable(predict_price)
    assert callable(predict_price_direction)


def test_offline_price_forecast():
    """
    Test Price Forecasting for Rice, Tomato, and Cotton.
    These use the validated Persistence baseline and do not require external foundation model loading.
    """
    for crop in ["rice", "tomato", "cotton"]:
        case = REAL_TEST_CASES[crop]
        res = predict_price(
            crop=case["crop"],
            market=case["market"],
            current_price=case["current_price"],
            date=case["date"]
        )
        assert "error" not in res, f"Unexpected error in {crop} forecast: {res}"
        assert res["crop"] == crop
        assert res["market"] == case["market"]
        assert res["forecast_method"] == "persistence"
        assert isinstance(res["predicted_price"], (int, float))
        assert res["predicted_price"] > 0
        assert "uncertainty" in res
        assert "lower_bound" in res["uncertainty"]
        assert "upper_bound" in res["uncertainty"]
        # Verify JSON serializability
        dumped = json.dumps(res)
        assert len(dumped) > 0


def test_chronos_price_forecast():
    """
    Test Price Forecasting for Wheat.
    This routes to Amazon Chronos-2 as validated in the ML experiments.
    """
    case = REAL_TEST_CASES["wheat"]
    res = predict_price(
        crop=case["crop"],
        market=case["market"],
        current_price=case["current_price"],
        date=case["date"]
    )
    assert "error" not in res, f"Unexpected error in wheat forecast: {res}"
    assert res["crop"] == "wheat"
    assert res["market"] == case["market"]
    assert res["forecast_method"] == "chronos-2"
    assert isinstance(res["predicted_price"], (int, float))
    assert res["predicted_price"] > 0
    assert "uncertainty" in res
    assert "lower_bound" in res["uncertainty"]
    assert "upper_bound" in res["uncertainty"]
    # Verify JSON serializability
    dumped = json.dumps(res)
    assert len(dumped) > 0


def test_price_direction_all_crops():
    """
    Test Price Direction inference across all 4 crops.
    Verifies that pre-trained classifiers return predicted direction and probabilities.
    """
    valid_directions = {"INCREASE", "STABLE", "DECREASE"}
    for crop, case in REAL_TEST_CASES.items():
        res = predict_price_direction(
            crop=case["crop"],
            market=case["market"],
            current_price=case["current_price"],
            date=case["date"]
        )
        assert "error" not in res, f"Unexpected error in {crop} direction: {res}"
        assert res["crop"] == crop
        assert res["market"] == case["market"]
        assert res["predicted_direction"] in valid_directions
        assert 0.0 <= res["confidence"] <= 1.0
        assert "probabilities" in res
        probs = res["probabilities"]
        assert "decrease" in probs and "stable" in probs and "increase" in probs
        prob_sum = probs["decrease"] + probs["stable"] + probs["increase"]
        assert 0.95 <= prob_sum <= 1.05  # Within rounding tolerance
        # Verify JSON serializability
        dumped = json.dumps(res)
        assert len(dumped) > 0


def test_invalid_crop():
    """Test handling of unsupported crops."""
    res_fc = predict_price(crop="mango", market="APMC Nagpur", current_price=1000.0, date="2025-05-15")
    assert "error" in res_fc
    assert "Unsupported crop" in res_fc["error"]

    res_dir = predict_price_direction(crop="mango", market="APMC Nagpur", current_price=1000.0, date="2025-05-15")
    assert "error" in res_dir
    assert "Unsupported crop" in res_dir["error"]


def test_invalid_price():
    """Test handling of invalid price inputs."""
    res_fc = predict_price(crop="wheat", market="APMC Nagpur", current_price=-500.0, date="2025-05-15")
    assert "error" in res_fc

    res_dir = predict_price_direction(crop="wheat", market="APMC Nagpur", current_price=0.0, date="2025-05-15")
    assert "error" in res_dir


def test_invalid_date():
    """Test handling of invalid dates."""
    res_dir = predict_price_direction(crop="wheat", market="APMC Nagpur", current_price=2650.0, date="")
    assert "error" in res_dir


def test_unknown_market_fallback():
    """
    Test graceful fallback when a market is not in the historical database.
    The system must fallback safely to persistence without crashing.
    """
    res_fc = predict_price(crop="wheat", market="Unknown APMC Market", current_price=2650.0, date="2025-05-15")
    assert "error" not in res_fc
    assert res_fc["predicted_price"] == 2650.0

    res_dir = predict_price_direction(crop="wheat", market="Unknown APMC Market", current_price=2650.0, date="2025-05-15")
    assert "error" not in res_dir
    assert res_dir["predicted_direction"] in {"INCREASE", "STABLE", "DECREASE"}


if __name__ == "__main__":
    print("Running MandiMitra ML Inference Tests...")
    test_imports()
    print("✓ test_imports passed")
    test_offline_price_forecast()
    print("✓ test_offline_price_forecast passed (Rice, Tomato, Cotton)")
    test_chronos_price_forecast()
    print("✓ test_chronos_price_forecast passed (Wheat)")
    test_price_direction_all_crops()
    print("✓ test_price_direction_all_crops passed (All 4 crops)")
    test_invalid_crop()
    print("✓ test_invalid_crop passed")
    test_invalid_price()
    print("✓ test_invalid_price passed")
    test_invalid_date()
    print("✓ test_invalid_date passed")
    test_unknown_market_fallback()
    print("✓ test_unknown_market_fallback passed")
    print("\nALL 8 TEST SUITES PASSED CLEANLY!")
