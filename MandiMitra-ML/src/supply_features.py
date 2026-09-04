"""
supply_features.py — MandiMitra Supply/Arrival Interface

Accepts optional external supply/arrival information.
Does NOT fabricate values. System works fully without supply data.
"""

from typing import Any, Dict, Optional

NOT_AVAILABLE = "NOT_AVAILABLE"


def validate_supply(supply_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate and normalize external supply/arrival data.

    Parameters
    ----------
    supply_data : dict or None with optional keys:
        arrival_quantity : float — tonnes/quintals arriving at mandi today
        arrival_change_pct : float — % change vs previous day/period
        market_supply_status : str — 'SURPLUS' | 'NORMAL' | 'DEFICIT'

    Returns
    -------
    dict with supply_status and validated fields
    """
    if not supply_data:
        return {"supply_status": NOT_AVAILABLE, "note": "No supply/arrival data provided."}

    validated = {"supply_status": "AVAILABLE"}
    warnings = []

    if "arrival_quantity" in supply_data:
        aq = supply_data["arrival_quantity"]
        if isinstance(aq, (int, float)) and aq >= 0:
            validated["arrival_quantity"] = float(aq)
        else:
            warnings.append(f"arrival_quantity invalid: {aq}; ignored.")

    if "arrival_change_pct" in supply_data:
        acp = supply_data["arrival_change_pct"]
        if isinstance(acp, (int, float)):
            validated["arrival_change_pct"] = float(acp)
        else:
            warnings.append(f"arrival_change_pct invalid: {acp}; ignored.")

    if "market_supply_status" in supply_data:
        mss = supply_data["market_supply_status"]
        if mss in ("SURPLUS", "NORMAL", "DEFICIT"):
            validated["market_supply_status"] = mss
        else:
            warnings.append(f"market_supply_status '{mss}' not in [SURPLUS, NORMAL, DEFICIT]; ignored.")

    if warnings:
        validated["warnings"] = warnings

    return validated


def supply_summary(validated_supply: Dict[str, Any]) -> str:
    """One-line supply summary for explanations."""
    if validated_supply.get("supply_status") == NOT_AVAILABLE:
        return "No arrival/supply data available."
    parts = []
    if "arrival_quantity" in validated_supply:
        parts.append(f"Arrivals: {validated_supply['arrival_quantity']:.0f} units")
    if "arrival_change_pct" in validated_supply:
        parts.append(f"Change: {validated_supply['arrival_change_pct']:+.1f}%")
    if "market_supply_status" in validated_supply:
        parts.append(f"Supply: {validated_supply['market_supply_status']}")
    return " | ".join(parts) if parts else "Supply data available but no notable conditions."


if __name__ == "__main__":
    tests = [
        None,
        {"arrival_quantity": 450, "arrival_change_pct": -15, "market_supply_status": "SURPLUS"},
        {"arrival_quantity": 200, "market_supply_status": "DEFICIT"},
        {"market_supply_status": "INVALID"},
    ]
    for t in tests:
        r = validate_supply(t)
        print(f"  Status: {r.get('supply_status')} | {supply_summary(r)}")
