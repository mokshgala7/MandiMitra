"""
decision_engine.py — MandiMitra Sell/Wait Decision Engine

The farmer's actual decision: SELL TODAY or WAIT.

Decision Logic:
===============
We use a normalized decision score:

    signal_strength = expected_change_pct / stability_threshold_pct

    where stability_threshold_pct = (validation_mae / current_price) * 100

This score answers: "Is the expected gain large enough relative to
the model's own prediction uncertainty?"

    signal_strength > 1.0  → expected change exceeds uncertainty → possible WAIT
    signal_strength ≤ 1.0  → expected change within noise band → SELL TODAY

Additional modifiers:
    - FALLING direction → always SELL TODAY
    - HIGH_VOLATILITY regime + small signal → SELL TODAY (uncertainty too high)
    - LOW_VOLATILITY + strong RISING signal → WAIT
    - STABLE direction → SELL TODAY (no meaningful upside)

The WAIT recommendation is reserved for cases where the expected improvement
is meaningfully larger than the historical forecast error — i.e., the signal
is strong enough to justify the risk of waiting.

Confidence classification:
    HIGH:   abs(signal_strength) > 2.0 and regime is LOW/MEDIUM
    MEDIUM: abs(signal_strength) > 1.0 or regime is MEDIUM
    LOW:    otherwise (high volatility, weak signal, or persistence fallback)
"""

from typing import Dict, Optional


def make_decision(
    direction: str,
    expected_change_pct: float,
    stability_threshold_pct: float,
    regime: str = "UNKNOWN",
    forecast_method: str = "persistence",
) -> Dict:
    """
    Generate SELL TODAY or WAIT recommendation with score and confidence.

    Parameters
    ----------
    direction : str — 'RISING' | 'STABLE' | 'FALLING'
    expected_change_pct : float — expected price change as %
    stability_threshold_pct : float — threshold % below which change is noise
    regime : str — 'LOW_VOLATILITY' | 'MEDIUM_VOLATILITY' | 'HIGH_VOLATILITY' | 'UNKNOWN'
    forecast_method : str — used to flag lower confidence for persistence

    Returns
    -------
    dict with recommendation, decision_score, confidence, reason
    """
    # Compute signal-to-noise ratio
    if stability_threshold_pct > 0:
        signal_strength = expected_change_pct / stability_threshold_pct
    else:
        signal_strength = 0.0

    # ── Primary decision logic ──────────────────────────────────
    if direction == "FALLING":
        recommendation = "SELL TODAY"
        primary_reason = f"Price is expected to fall by {abs(expected_change_pct):.1f}%. Selling today captures the current price."

    elif direction == "STABLE":
        recommendation = "SELL TODAY"
        primary_reason = (
            f"Expected price change ({expected_change_pct:.1f}%) is within the historical "
            f"forecast uncertainty band (±{stability_threshold_pct:.1f}%). "
            "No meaningful upside justifies waiting."
        )

    elif direction == "RISING":
        # WAIT only if signal is strong enough and volatility not too high
        if regime == "HIGH_VOLATILITY" and signal_strength < 2.0:
            recommendation = "SELL TODAY"
            primary_reason = (
                f"Although price is expected to rise ({expected_change_pct:.1f}%), "
                f"high market volatility makes the forecast unreliable. "
                "Selling today is the safer choice."
            )
        elif signal_strength >= 1.5:
            recommendation = "WAIT"
            primary_reason = (
                f"Price is expected to rise by approximately {expected_change_pct:.1f}%, "
                f"which is {signal_strength:.1f}× larger than the historical forecast uncertainty "
                f"(threshold {stability_threshold_pct:.1f}%). Waiting may capture a higher price."
            )
        else:
            recommendation = "SELL TODAY"
            primary_reason = (
                f"Price is expected to rise ({expected_change_pct:.1f}%), but the expected gain "
                f"(signal strength {signal_strength:.2f}×) is not sufficiently larger than the "
                f"historical forecast uncertainty to justify the risk of waiting."
            )
    else:
        recommendation = "SELL TODAY"
        primary_reason = "Direction is unknown. Recommend selling to avoid uncertainty."

    # ── Confidence classification ───────────────────────────────
    if abs(signal_strength) > 2.0 and regime in ("LOW_VOLATILITY", "MEDIUM_VOLATILITY"):
        confidence = "HIGH"
    elif abs(signal_strength) > 1.0 or regime == "MEDIUM_VOLATILITY":
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    # Persistence-based forecasts are inherently less informative
    if forecast_method == "persistence" and confidence == "HIGH":
        confidence = "MEDIUM"

    return {
        "recommendation": recommendation,
        "decision_score": round(signal_strength, 4),
        "confidence": confidence,
        "reason": primary_reason,
        "direction": direction,
        "expected_change_pct": round(expected_change_pct, 4),
        "stability_threshold_pct": round(stability_threshold_pct, 4),
        "regime": regime,
    }


if __name__ == "__main__":
    tests = [
        ("RISING", 5.2, 2.5, "LOW_VOLATILITY", "ml_model"),
        ("RISING", 1.1, 2.5, "MEDIUM_VOLATILITY", "persistence"),
        ("FALLING", -3.0, 2.5, "MEDIUM_VOLATILITY", "persistence"),
        ("STABLE", 0.5, 2.5, "LOW_VOLATILITY", "persistence"),
        ("RISING", 8.0, 3.0, "HIGH_VOLATILITY", "ml_model"),
    ]
    for args in tests:
        r = make_decision(*args)
        print(f"  {args[0]} {args[1]:.1f}% | {r['recommendation']} (conf={r['confidence']}, score={r['decision_score']})")
