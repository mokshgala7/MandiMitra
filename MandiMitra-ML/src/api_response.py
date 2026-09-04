"""
api_response.py — MandiMitra API Response Schema

Defines the stable JSON-compatible output schema for the backend team.
All fields are explicitly typed. Missing/unavailable values use null or "NOT_AVAILABLE".
"""

import json
from typing import Any, Dict, List, Optional, Union


NOT_AVAILABLE = "NOT_AVAILABLE"


def build_api_response(
    crop: str,
    market: str,
    current_price: float,
    forecast_method: str,
    predicted_price: float,
    forecast_lower_bound: Optional[float],
    forecast_upper_bound: Optional[float],
    expected_change: float,
    expected_change_pct: float,
    direction: str,
    volatility_regime: str,
    confidence: str,
    best_market: Optional[str],
    best_market_price: Optional[float],
    transport_cost: Optional[float],
    best_market_net_price: Optional[float],
    recommendation: str,
    reason: str,
    data_warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Build standardized API response dict.

    All float fields are rounded to 2 decimal places.
    Missing values are None or "NOT_AVAILABLE" — never fabricated.
    """

    def _r(v):
        """Round floats, pass None and NOT_AVAILABLE unchanged."""
        if v is None or v == NOT_AVAILABLE:
            return v
        try:
            return round(float(v), 2)
        except (TypeError, ValueError):
            return v

    return {
        # Core identification
        "crop": str(crop).lower(),
        "market": str(market),

        # Price context
        "current_price": _r(current_price),

        # Forecast
        "forecast_method": str(forecast_method),
        "predicted_price": _r(predicted_price),
        "forecast_lower_bound": _r(forecast_lower_bound),
        "forecast_upper_bound": _r(forecast_upper_bound),

        # Price change
        "expected_change": _r(expected_change),
        "expected_change_pct": _r(expected_change_pct),
        "direction": str(direction),

        # Market conditions
        "volatility_regime": str(volatility_regime),
        "confidence": str(confidence),

        # Market comparison
        "best_market": best_market if best_market is not None else NOT_AVAILABLE,
        "best_market_price": _r(best_market_price) if best_market_price is not None else NOT_AVAILABLE,
        "transport_cost": _r(transport_cost) if transport_cost is not None else NOT_AVAILABLE,
        "best_market_net_price": _r(best_market_net_price) if best_market_net_price not in (None, NOT_AVAILABLE) else NOT_AVAILABLE,

        # Decision
        "recommendation": str(recommendation),
        "reason": str(reason),

        # Data quality
        "data_warnings": data_warnings or [],
    }


def response_to_json(response: Dict[str, Any], indent: int = 2) -> str:
    """Serialize API response to JSON string."""
    return json.dumps(response, indent=indent, ensure_ascii=False, default=str)


if __name__ == "__main__":
    example = build_api_response(
        crop="wheat",
        market="APMC Sillod",
        current_price=2500,
        forecast_method="persistence",
        predicted_price=2500,
        forecast_lower_bound=2433.09,
        forecast_upper_bound=2566.91,
        expected_change=0,
        expected_change_pct=0.0,
        direction="STABLE",
        volatility_regime="LOW_VOLATILITY",
        confidence="MEDIUM",
        best_market="APMC Sillod",
        best_market_price=2500,
        transport_cost=None,
        best_market_net_price=None,
        recommendation="SELL TODAY",
        reason="Price is expected to remain stable. No meaningful upside justifies waiting.",
        data_warnings=[],
    )
    print(response_to_json(example))
