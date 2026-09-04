from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class NearbyMandiItem(BaseModel):
    mandi_id: str
    mandi_name: str
    district: str
    state: str
    latitude: float
    longitude: float
    distance_km: float
    latest_price: float
    price_unit: str = "Rs./Quintal"
    price_date: str

class LocationCoordinates(BaseModel):
    latitude: float
    longitude: float

class NearbyMeta(BaseModel):
    total_price_records_checked: int
    total_master_records: int
    records_missing_coordinates: int

class NearbyMandisResponse(BaseModel):
    crop: str
    radius_km: float
    farmer_location: LocationCoordinates
    meta: NearbyMeta
    mandis: List[NearbyMandiItem]
