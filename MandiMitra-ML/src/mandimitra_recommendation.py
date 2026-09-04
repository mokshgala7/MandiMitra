"""
mandimitra_recommendation.py — MandiMitra Final Recommendation Engine

Main AI decision interface.
Integrates: forecast → direction → uncertainty → regime → decision → market comparison → explanation → API response.

Usage:
    from src.mandimitra_recommendation import get_recommendation
    result = get_recommendation(crop="wheat", market="APMC Sillod", current_price=2500, historical_features={...})
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent

from src.forecast_engine import (
    forecast_price, load_forecast_config, load_metadata,
    _normalize_crop, SUPPORTED_CROPS
)
from src.price_direction import classify_direction
from src.decision_engine import make_decision
from src.market_comparison import compare_markets
from src.market_regime import classify_regime
from src.weather_features import validate_weather, weather_summary
from src.supply_features import validate_supply, supply_summary
from src.explanation import generate_explanation
from src.api_response import build_api_response, NOT_AVAILABLE


# ── Uncertainty estimation ────────────────────────────────────────
def estimate_uncertainty(
    predicted_price: float,
    validation_mae: Optional[float],
    regime: str,
    forecast_method: str,
    z_score: float = 1.0,
) -> Dict[str, Any]:
    """
    Estimate prediction interval from empirical validation MAE.

    Method:
        The model's out-of-sample MAE is used as the uncertainty scale.
        A ±z_score × MAE band gives an approximate interval containing
        ~68% of historical errors (for z=1) — not a Gaussian assumption,
        but a conservative empirical band.

    For HIGH_VOLATILITY, the band is widened by ×1.5.
    For persistence, we use the persistence baseline MAE.

    Returns
    -------
    dict with lower_bound, upper_bound, uncertainty, confidence_level
    """
    if validation_mae is None or validation_mae <= 0:
        return {
            "lower_bound": None,
            "upper_bound": None,
            "uncertainty": NOT_AVAILABLE,
            "confidence_level": "LOW",
            "interval_method": "unavailable",
        }

    scale = validation_mae
    if regime == "HIGH_VOLATILITY":
        scale *= 1.5

    lower = predicted_price - z_score * scale
    upper = predicted_price + z_score * scale
    uncertainty_pct = (scale / predicted_price) * 100 if predicted_price > 0 else 0

    # Confidence: based on relative uncertainty
    if uncertainty_pct < 3.0 and regime != "HIGH_VOLATILITY":
        conf = "HIGH"
    elif uncertainty_pct < 8.0 and regime != "HIGH_VOLATILITY":
        conf = "MEDIUM"
    else:
        conf = "LOW"

    if forecast_method == "persistence" and conf == "HIGH":
        conf = "MEDIUM"

    return {
        "lower_bound": round(lower, 2),
        "upper_bound": round(upper, 2),
        "uncertainty_mae_scale": round(scale, 2),
        "uncertainty_pct": round(uncertainty_pct, 4),
        "confidence_level": conf,
        "interval_method": f"empirical_mae_band z={z_score}, regime_adjusted={regime}",
    }


# ── Main recommendation function ─────────────────────────────────

def get_recommendation(
    crop: str,
    market: str,
    current_price: float,
    historical_features: Union[Dict[str, Any], None] = None,
    recent_prices: Optional[List[float]] = None,
    nearby_markets: Optional[List[Dict[str, Any]]] = None,
    transport_data: Optional[Dict[str, Any]] = None,
    weather_data: Optional[Dict[str, Any]] = None,
    supply_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate full MandiMitra recommendation.

    Parameters
    ----------
    crop : str — one of rice/tomato/wheat/cotton
    market : str — current mandi name
    current_price : float — today's Modal Price (₹/quintal)
    historical_features : dict or None — full feature dict for ML inference
        (Required for ml_model method; falls back to persistence if absent)
    recent_prices : list of float or None — recent Modal Prices oldest-first
        (Used for regime detection; if None, regime = UNKNOWN)
    nearby_markets : list or None — each: {market, current_price, transport_cost_per_quintal}
    transport_data : dict or None — {transport_cost_per_quintal: float}
    weather_data : dict or None — weather fields
    supply_data : dict or None — supply/arrival fields

    Returns
    -------
    Full API response dict (see api_response.py schema)
    """
    data_warnings = []

    # ── 1. Validate crop ─────────────────────────────────────
    try:
        crop_norm = _normalize_crop(crop)
    except ValueError as e:
        raise ValueError(str(e))

    # ── 2. Validate price ────────────────────────────────────
    if not isinstance(current_price, (int, float)) or current_price <= 0:
        raise ValueError(f"current_price must be a positive number, got: {current_price}")

    # ── 3. Load metadata ─────────────────────────────────────
    meta = load_metadata(crop_norm)
    validation_mae = meta.get("MAE", meta.get("persistence_baseline_MAE"))
    persistence_mae = meta.get("persistence_baseline_MAE", validation_mae)

    # ── 4. Forecast ──────────────────────────────────────────
    config = load_forecast_config()
    selected_method = config.get(crop_norm, {}).get("method", "persistence")

    if selected_method == "ml_model" and historical_features is None:
        data_warnings.append("ML model selected but no historical_features provided; falling back to persistence.")
        selected_method = "persistence_fallback_no_features"

    try:
        if historical_features is not None:
            forecast_result = forecast_price(crop_norm, market, historical_features, override_method=selected_method)
        else:
            forecast_result = forecast_price(crop_norm, market, {"Modal Price": current_price, "price_ma_7": None}, override_method="persistence")
    except Exception as e:
        data_warnings.append(f"Forecast error ({type(e).__name__}): {e}. Falling back to persistence.")
        forecast_result = {
            "forecast_method": "persistence_fallback",
            "predicted_price": current_price,
            "validation_mae": persistence_mae,
        }

    predicted_price = forecast_result["predicted_price"]
    forecast_method_used = forecast_result["forecast_method"]

    # ── 5. Direction ─────────────────────────────────────────
    direction_result = classify_direction(
        current_price=current_price,
        predicted_price=predicted_price,
        validation_mae=validation_mae,
    )
    direction = direction_result["direction"]
    expected_change_pct = direction_result["expected_change_pct"]
    stability_threshold_pct = direction_result["stability_threshold_pct"]
    expected_change_abs = direction_result["expected_change_abs"]

    # ── 6. Regime ────────────────────────────────────────────
    prices_for_regime = recent_prices or ([current_price] * 5)
    if len(prices_for_regime) < 3:
        data_warnings.append("Fewer than 3 recent prices provided; regime detection may be unreliable.")
    regime_result = classify_regime(prices_for_regime)
    regime = regime_result["regime"]

    # ── 7. Uncertainty ───────────────────────────────────────
    unc = estimate_uncertainty(predicted_price, validation_mae, regime, forecast_method_used)
    confidence = unc["confidence_level"]

    # ── 8. Market comparison ─────────────────────────────────
    home_tc = None
    if transport_data and isinstance(transport_data.get("transport_cost_per_quintal"), (int, float)):
        home_tc = float(transport_data["transport_cost_per_quintal"])

    market_result = compare_markets(
        crop=crop_norm,
        home_market=market,
        home_price=current_price,
        nearby_markets=nearby_markets,
        home_transport_cost=home_tc,
    )
    best_market = market_result["best_market"]
    best_gross = market_result["best_gross_price"]
    best_net_raw = market_result["best_net_price"]
    best_net = None if best_net_raw == NOT_AVAILABLE else best_net_raw

    # ── 9. Decision ──────────────────────────────────────────
    decision_result = make_decision(
        direction=direction,
        expected_change_pct=expected_change_pct,
        stability_threshold_pct=stability_threshold_pct,
        regime=regime,
        forecast_method=forecast_method_used,
    )
    recommendation = decision_result["recommendation"]
    decision_score = decision_result["decision_score"]

    # If a better market exists with higher net price, prefer SELL at best market
    if best_market != market and best_net is not None and best_net > current_price:
        if recommendation != "WAIT":
            recommendation = "SELL TODAY"
            data_warnings.append(f"Better net price available at {best_market}.")

    # ── 10. Explanation ──────────────────────────────────────
    wx = validate_weather(weather_data)
    sx = validate_supply(supply_data)
    wx_summary = weather_summary(wx)
    sx_summary = supply_summary(sx)

    reason = generate_explanation(
        recommendation=recommendation,
        direction=direction,
        expected_change_pct=expected_change_pct,
        current_price=current_price,
        predicted_price=predicted_price,
        confidence=confidence,
        decision_score=decision_score,
        stability_threshold_pct=stability_threshold_pct,
        regime=regime,
        forecast_method=forecast_method_used,
        best_market=best_market,
        best_net_price=best_net,
        home_market=market,
        weather_summary=wx_summary,
        supply_summary=sx_summary,
        data_warnings=data_warnings,
    )

    # ── 11. Build API response ───────────────────────────────
    response = build_api_response(
        crop=crop_norm,
        market=market,
        current_price=current_price,
        forecast_method=forecast_method_used,
        predicted_price=predicted_price,
        forecast_lower_bound=unc["lower_bound"],
        forecast_upper_bound=unc["upper_bound"],
        expected_change=expected_change_abs,
        expected_change_pct=expected_change_pct,
        direction=direction,
        volatility_regime=regime,
        confidence=confidence,
        best_market=best_market,
        best_market_price=best_gross,
        transport_cost=home_tc,
        best_market_net_price=best_net,
        recommendation=recommendation,
        reason=reason,
        data_warnings=data_warnings,
    )

    return response


if __name__ == "__main__":
    # Quick smoke test with persistence
    result = get_recommendation(
        crop="wheat",
        market="APMC Sillod",
        current_price=2500,
        recent_prices=[2480, 2490, 2500, 2510, 2500, 2490, 2500, 2500, 2510, 2500],
    )
    import json
    print(json.dumps(result, indent=2))
