"""
explanation.py — MandiMitra Farmer-Friendly Explanation Generator

Generates concise, human-readable explanations from actual calculated values.
Never fabricates reasons — all text is derived from real decision inputs.
"""

from typing import Any, Dict, Optional


def generate_explanation(
    recommendation: str,
    direction: str,
    expected_change_pct: float,
    current_price: float,
    predicted_price: float,
    confidence: str,
    decision_score: float,
    stability_threshold_pct: float,
    regime: str,
    forecast_method: str,
    best_market: Optional[str] = None,
    best_net_price: Optional[float] = None,
    home_market: Optional[str] = None,
    weather_summary: Optional[str] = None,
    supply_summary: Optional[str] = None,
    data_warnings: Optional[list] = None,
) -> str:
    """
    Generate a farmer-friendly explanation from actual decision values.

    All text is derived from the calculated inputs — no hardcoded generic phrases.
    """
    lines = []

    # ── Price forecast ────────────────────────────────────────
    change_abs = predicted_price - current_price
    if direction == "RISING":
        lines.append(
            f"Price is expected to rise by approximately ₹{abs(change_abs):.0f}/quintal "
            f"({abs(expected_change_pct):.1f}%) over the next ~3 market observations."
        )
    elif direction == "FALLING":
        lines.append(
            f"Price is expected to fall by approximately ₹{abs(change_abs):.0f}/quintal "
            f"({abs(expected_change_pct):.1f}%) over the next ~3 market observations."
        )
    else:  # STABLE
        lines.append(
            f"Price is expected to remain approximately stable "
            f"(change of {expected_change_pct:+.1f}%, within the ±{stability_threshold_pct:.1f}% uncertainty band)."
        )

    # ── Signal strength ──────────────────────────────────────
    if direction == "RISING":
        if decision_score >= 1.5:
            lines.append(
                f"The expected price increase ({expected_change_pct:.1f}%) is "
                f"{decision_score:.1f}× larger than the model's historical forecast uncertainty "
                f"(threshold ±{stability_threshold_pct:.1f}%), suggesting a meaningful signal."
            )
        else:
            lines.append(
                f"The expected rise ({expected_change_pct:.1f}%) is only {decision_score:.2f}× the uncertainty band "
                f"(±{stability_threshold_pct:.1f}%), which is not strong enough to justify waiting."
            )

    # ── Volatility ────────────────────────────────────────────
    if regime == "HIGH_VOLATILITY":
        lines.append(
            "The market is currently in a high-volatility state, making price forecasts less reliable."
        )
    elif regime == "LOW_VOLATILITY":
        lines.append("Market conditions are stable, supporting more reliable forecasts.")

    # ── Market comparison ────────────────────────────────────
    if best_market and home_market and best_market != home_market and best_net_price not in (None, "NOT_AVAILABLE"):
        lines.append(
            f"Nearby mandi '{best_market}' offers a higher estimated net price of "
            f"₹{best_net_price:.0f}/quintal after transport costs."
        )
    elif best_market and best_market == home_market:
        lines.append(f"Your current mandi ({home_market}) offers the best available net price.")

    # ── Forecast method note ─────────────────────────────────
    if "persistence" in forecast_method:
        lines.append(
            "Forecast is based on persistence (current price as best estimate of near-term price)."
        )

    # ── Weather/supply context (if available) ────────────────
    if weather_summary and "NOT_AVAILABLE" not in weather_summary and "No weather" not in weather_summary:
        lines.append(f"Weather context: {weather_summary}")
    if supply_summary and "NOT_AVAILABLE" not in supply_summary and "No arrival" not in supply_summary:
        lines.append(f"Supply context: {supply_summary}")

    # ── Recommendation conclusion ────────────────────────────
    if recommendation == "SELL TODAY":
        lines.append(
            "Recommendation: Sell today to secure the current price."
        )
    else:
        lines.append(
            "Recommendation: Consider waiting for a potentially better price, "
            "though market conditions can change."
        )

    # ── Data warnings ─────────────────────────────────────────
    if data_warnings:
        lines.append(f"Data note: {'; '.join(data_warnings)}")

    return " ".join(lines)


if __name__ == "__main__":
    exp = generate_explanation(
        recommendation="WAIT",
        direction="RISING",
        expected_change_pct=4.2,
        current_price=2500,
        predicted_price=2605,
        confidence="MEDIUM",
        decision_score=1.68,
        stability_threshold_pct=2.5,
        regime="LOW_VOLATILITY",
        forecast_method="persistence",
        best_market="APMC Sillod",
        home_market="APMC Sillod",
    )
    print(exp)
