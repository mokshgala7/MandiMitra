from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class RecommendationRequest(BaseModel):
    crop: str
    quantity_kg: float
    latitude: float
    longitude: float
    has_middleman: bool = False
    middleman_price: Optional[float] = None
    middleman_commission: Optional[float] = None
    middleman_other: Optional[float] = None
    radius_km: float = 500.0

class MandiEconomics(BaseModel):
    mandi_id: str
    mandi_name: str
    distance_km: float
    price_per_quintal: float
    transport_cost: float
    gross_value: float
    net_value: float

class MiddlemanEconomics(BaseModel):
    price_per_quintal: float
    commission: float
    other_charges: float
    gross_value: float
    net_value: float

class RecommendationResponse(BaseModel):
    recommendation: str  # "SELL TODAY" | "HOLD FOR 2-3 DAYS"
    reason: str
    crop: str
    quantity_kg: float
    quantity_quintals: float
    best_mandi: Optional[MandiEconomics] = None
    middleman: Optional[MiddlemanEconomics] = None
    current_net_value: float
    expected_future_price: float
    expected_future_net_value: float
    potential_difference: float
    trend: str
    weather_advisory: Optional[str] = None
