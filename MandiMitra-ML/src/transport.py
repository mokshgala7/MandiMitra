"""
transport.py — MandiMitra Transport Cost Interface

Provides a clean interface for calculating transport costs.
Does NOT fabricate distances or costs — all values must be externally supplied.

Design rationale:
    Transport data is farm- and vehicle-specific. This module accepts
    externally provided transport cost (e.g., from the backend or farmer input)
    and uses it to compute net price. It does not invent estimates.
"""

from typing import Any, Dict, Optional, Union


NOT_AVAILABLE = "NOT_AVAILABLE"


def calculate_transport_cost(
    farmer_location: Optional[str] = None,
    mandi_location: Optional[str] = None,
    vehicle_type: Optional[str] = None,
    quantity_quintals: Optional[float] = None,
    transport_cost_per_quintal: Optional[float] = None,
    transport_cost_total: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calculate transport cost given externally supplied cost data.

    At least one of transport_cost_per_quintal or transport_cost_total must be provided.
    If neither is available, returns a NOT_AVAILABLE response.

    Parameters
    ----------
    farmer_location : str — farmer's village/location (for logging only)
    mandi_location : str — destination mandi (for logging only)
    vehicle_type : str — e.g. 'tractor', 'truck' (for logging only)
    quantity_quintals : float — crop quantity in quintals
    transport_cost_per_quintal : float — ₹ cost per quintal (external input)
    transport_cost_total : float — ₹ total transport cost (external input, overrides per_quintal)

    Returns
    -------
    dict with transport cost details
    """
    if transport_cost_total is not None:
        total_cost = float(transport_cost_total)
        per_quintal = (total_cost / quantity_quintals) if quantity_quintals else None
        source = "transport_cost_total"
    elif transport_cost_per_quintal is not None:
        per_quintal = float(transport_cost_per_quintal)
        total_cost = (per_quintal * quantity_quintals) if quantity_quintals else None
        source = "transport_cost_per_quintal"
    else:
        return {
            "status": NOT_AVAILABLE,
            "farmer_location": farmer_location,
            "mandi_location": mandi_location,
            "transport_cost_per_quintal": NOT_AVAILABLE,
            "transport_cost_total": NOT_AVAILABLE,
            "note": "No transport cost data provided. Supply transport_cost_per_quintal or transport_cost_total.",
        }

    return {
        "status": "AVAILABLE",
        "farmer_location": farmer_location,
        "mandi_location": mandi_location,
        "vehicle_type": vehicle_type,
        "quantity_quintals": quantity_quintals,
        "transport_cost_per_quintal": round(per_quintal, 2) if per_quintal is not None else NOT_AVAILABLE,
        "transport_cost_total": round(total_cost, 2) if total_cost is not None else NOT_AVAILABLE,
        "source": source,
    }


def compute_net_price(
    gross_price: float,
    transport_cost_per_quintal: Union[float, str],
) -> Dict[str, Any]:
    """
    Compute net price after transport cost.

    Parameters
    ----------
    gross_price : float — mandi selling price (₹/quintal)
    transport_cost_per_quintal : float or "NOT_AVAILABLE"

    Returns
    -------
    dict with gross_price, transport_cost, net_price
    """
    if transport_cost_per_quintal == NOT_AVAILABLE or transport_cost_per_quintal is None:
        return {
            "gross_price": round(gross_price, 2),
            "transport_cost_per_quintal": NOT_AVAILABLE,
            "net_price": NOT_AVAILABLE,
            "note": "Net price unavailable — transport cost not provided.",
        }

    tc = float(transport_cost_per_quintal)
    net = gross_price - tc
    return {
        "gross_price": round(gross_price, 2),
        "transport_cost_per_quintal": round(tc, 2),
        "net_price": round(net, 2),
    }


if __name__ == "__main__":
    # Example: transport cost supplied externally
    r = calculate_transport_cost(
        farmer_location="Hinganghat Village",
        mandi_location="APMC Hinganghat",
        vehicle_type="tractor",
        quantity_quintals=20,
        transport_cost_per_quintal=50,
    )
    print(r)
    print(compute_net_price(7200, 50))
    print(compute_net_price(7200, "NOT_AVAILABLE"))
