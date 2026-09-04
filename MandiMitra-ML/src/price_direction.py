"""
price_direction.py — MandiMitra Price Direction Classifier
Classifies expected price movement as RISING, STABLE, or FALLING.

Threshold derivation:
    The stability band is set to ±historical_validation_MAE / current_price.
    Any expected change within this band is classified STABLE, because the
    expected change is smaller than the model's own empirical error — it is
    statistically indistinguishable from "no change".
    Outside this band, RISING (positive) or FALLING (negative).
"""

from typing import Dict, Optional


# Default stability threshold (% change) used when no historical error is available.
# Derived from the average relative MAE across all four crops ≈ 3%.
DEFAULT_STABILITY_THRESHOLD_PCT = 3.0


def classify_direction(
    current_price: float,
    predicted_price: float,
    validation_mae: Optional[float] = None,
    stability_threshold_pct: Optional[float] = None,
) -> Dict:
    """
    Classify expected price direction.

    Parameters
    ----------
    current_price : float — today's Modal Price
    predicted_price : float — forecast price ~3 obs ahead
    validation_mae : float, optional — historical out-of-sample MAE (₹)
        Used to derive a data-driven stability threshold.
    stability_threshold_pct : float, optional — override threshold (%).
        If None, derived from validation_mae or DEFAULT_STABILITY_THRESHOLD_PCT.

    Returns
    -------
    dict with direction, expected_change_abs, expected_change_pct, threshold_used_pct
    """
    if current_price <= 0:
        raise ValueError("current_price must be positive.")

    expected_change_abs = predicted_price - current_price
    expected_change_pct = (expected_change_abs / current_price) * 100

    # Derive threshold
    if stability_threshold_pct is not None:
        threshold_pct = stability_threshold_pct
        threshold_source = "override"
    elif validation_mae is not None and current_price > 0:
        # Data-driven: express MAE as % of current price
        # Any change smaller than MAE/price is within the model's own error margin
        threshold_pct = (validation_mae / current_price) * 100
        threshold_source = f"validation_mae={validation_mae:.2f}"
    else:
        threshold_pct = DEFAULT_STABILITY_THRESHOLD_PCT
        threshold_source = "default"

    # Classify
    if expected_change_pct > threshold_pct:
        direction = "RISING"
    elif expected_change_pct < -threshold_pct:
        direction = "FALLING"
    else:
        direction = "STABLE"

    return {
        "direction": direction,
        "expected_change_abs": round(expected_change_abs, 2),
        "expected_change_pct": round(expected_change_pct, 4),
        "stability_threshold_pct": round(threshold_pct, 4),
        "threshold_source": threshold_source,
    }


if __name__ == "__main__":
    examples = [
        (2500, 2600, 80),
        (2500, 2510, 70),
        (2500, 2400, 70),
        (7200, 7250, 104),
    ]
    for cp, pp, mae in examples:
        r = classify_direction(cp, pp, validation_mae=mae)
        print(f"  {cp} → {pp}: {r['direction']} ({r['expected_change_pct']:.2f}% | threshold {r['stability_threshold_pct']:.2f}%)")
