"""
market_comparison.py — MandiMitra Market Comparison Module

Ranks nearby markets by net selling price (gross price minus transport cost).
If transport data is unavailable, ranks by gross price only.
Never fabricates prices or transport costs.
"""

from typing import Any, Dict, List, Optional, Union
from src.transport import compute_net_price, NOT_AVAILABLE


def compare_markets(
    crop: str,
    home_market: str,
    home_price: float,
    nearby_markets: Optional[List[Dict[str, Any]]] = None,
    home_transport_cost: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Compare home market with nearby markets and rank by net price.

    Parameters
    ----------
    crop : str
    home_market : str — current market name
    home_price : float — current market Modal Price (₹/quintal)
    nearby_markets : list of dicts, each with:
        {
            "market": str,
            "current_price": float,
            "transport_cost_per_quintal": float or "NOT_AVAILABLE"
        }
    home_transport_cost : float or None — transport cost to reach home market

    Returns
    -------
    dict with ranked_markets and best_market recommendation
    """
    all_markets = []

    # Home market
    home_net = compute_net_price(home_price, home_transport_cost or NOT_AVAILABLE)
    all_markets.append({
        "market": home_market,
        "is_home_market": True,
        "current_price": round(home_price, 2),
        "transport_cost_per_quintal": home_net["transport_cost_per_quintal"],
        "net_price": home_net["net_price"],
        "note": "Current market",
    })

    # Nearby markets
    if nearby_markets:
        for nm in nearby_markets:
            mkt_name = nm.get("market", "Unknown")
            mkt_price = float(nm.get("current_price", 0))
            tc = nm.get("transport_cost_per_quintal", NOT_AVAILABLE)
            net_result = compute_net_price(mkt_price, tc)
            all_markets.append({
                "market": mkt_name,
                "is_home_market": False,
                "current_price": round(mkt_price, 2),
                "transport_cost_per_quintal": net_result["transport_cost_per_quintal"],
                "net_price": net_result["net_price"],
                "note": nm.get("note", ""),
            })

    # Rank: prefer net_price if available, else gross price
    def sort_key(m):
        np_val = m["net_price"]
        if np_val == NOT_AVAILABLE:
            return m["current_price"]
        return float(np_val)

    ranked = sorted(all_markets, key=sort_key, reverse=True)

    # Determine best market
    best = ranked[0]
    transport_available = any(m["net_price"] != NOT_AVAILABLE for m in ranked)

    return {
        "crop": crop,
        "ranking_basis": "net_price" if transport_available else "gross_price",
        "ranked_markets": ranked,
        "best_market": best["market"],
        "best_gross_price": best["current_price"],
        "best_net_price": best["net_price"],
        "transport_data_available": transport_available,
    }


if __name__ == "__main__":
    result = compare_markets(
        crop="wheat",
        home_market="APMC Sillod",
        home_price=2500,
        nearby_markets=[
            {"market": "APMC Aurangabad", "current_price": 2600, "transport_cost_per_quintal": 80},
            {"market": "APMC Jalna", "current_price": 2650, "transport_cost_per_quintal": 130},
        ],
        home_transport_cost=0,
    )
    print("Ranked Markets:")
    for m in result["ranked_markets"]:
        print(f"  {m['market']}: gross=₹{m['current_price']} | net=₹{m['net_price']}")
    print(f"Best: {result['best_market']}")
