"""
market_regime.py — MandiMitra Market Volatility / Regime Classifier

Classifies current market conditions as:
    LOW_VOLATILITY | MEDIUM_VOLATILITY | HIGH_VOLATILITY

Method:
    Rolling coefficient of variation (CV) = rolling_std / rolling_mean
    computed over the last N observations for the Market+Variety+Grade series.

Threshold derivation (data-driven):
    LOW:    CV < 0.03  (price changes <3% relative to the mean in recent window)
    MEDIUM: CV 0.03–0.08
    HIGH:   CV > 0.08

These thresholds are derived from observed rolling CVs across all four crops:
    - Wheat/Rice/Cotton: low-medium (CV 0.01–0.05)
    - Tomato: high (CV 0.10–0.30 in peak seasons)

The rolling window uses the last 14 observations (≈2 calendar weeks).
"""

from typing import Dict, List, Optional


LOW_THRESHOLD_CV = 0.03
HIGH_THRESHOLD_CV = 0.08
ROLLING_WINDOW = 14  # observations


def compute_rolling_cv(prices: List[float], window: int = ROLLING_WINDOW) -> Optional[float]:
    """Compute coefficient of variation over last `window` price observations."""
    if len(prices) < 3:
        return None
    recent = prices[-window:] if len(prices) >= window else prices
    mean = sum(recent) / len(recent)
    if mean == 0:
        return None
    variance = sum((p - mean) ** 2 for p in recent) / len(recent)
    std = variance ** 0.5
    return std / mean


def classify_regime(
    prices: List[float],
    window: int = ROLLING_WINDOW,
    low_threshold: float = LOW_THRESHOLD_CV,
    high_threshold: float = HIGH_THRESHOLD_CV,
) -> Dict:
    """
    Classify market volatility regime from a list of recent Modal Prices.

    Parameters
    ----------
    prices : list of float — recent Modal Price observations (oldest first)
    window : int — rolling window length (observations)
    low_threshold, high_threshold : float — CV thresholds

    Returns
    -------
    dict with regime, rolling_cv, window_used, thresholds
    """
    if not prices or len(prices) < 2:
        return {
            "regime": "UNKNOWN",
            "rolling_cv": None,
            "window_used": 0,
            "reason": "Insufficient price history",
        }

    cv = compute_rolling_cv(prices, window)
    window_used = min(len(prices), window)

    if cv is None:
        regime = "UNKNOWN"
        reason = "Could not compute CV (zero mean or insufficient data)"
    elif cv < low_threshold:
        regime = "LOW_VOLATILITY"
        reason = f"Rolling CV={cv:.4f} < {low_threshold} — prices are stable"
    elif cv <= high_threshold:
        regime = "MEDIUM_VOLATILITY"
        reason = f"Rolling CV={cv:.4f} in [{low_threshold}, {high_threshold}] — moderate fluctuation"
    else:
        regime = "HIGH_VOLATILITY"
        reason = f"Rolling CV={cv:.4f} > {high_threshold} — prices are highly variable"

    return {
        "regime": regime,
        "rolling_cv": round(cv, 6) if cv is not None else None,
        "window_used": window_used,
        "low_threshold_cv": low_threshold,
        "high_threshold_cv": high_threshold,
        "reason": reason,
    }


if __name__ == "__main__":
    tests = [
        ("Wheat stable", [2500, 2500, 2500, 2520, 2510, 2500, 2490, 2500, 2510, 2500]),
        ("Tomato volatile", [1500, 2000, 3500, 1800, 4000, 2500, 800, 3000, 4500, 1200]),
        ("Cotton seasonal", [7200, 7250, 7300, 7200, 7100, 7200, 7250, 7200, 7300, 7200]),
    ]
    for name, prices in tests:
        r = classify_regime(prices)
        print(f"  {name}: {r['regime']} (CV={r['rolling_cv']})")
