from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class SearchCreate(BaseModel):
    crop: str
    quantity_kg: float
    latitude: float
    longitude: float
    selected_mandi_id: Optional[str] = None
    has_middleman: bool = False
    middleman_price: Optional[float] = None
    middleman_commission: Optional[float] = None
    middleman_other: Optional[float] = None
    recommendation: Optional[str] = None

class SearchOut(BaseModel):
    id: int
    crop: str
    quantity_kg: float
    latitude: float
    longitude: float
    selected_mandi_id: Optional[str] = None
    has_middleman: bool
    middleman_price: Optional[float] = None
    middleman_commission: Optional[float] = None
    middleman_other: Optional[float] = None
    recommendation: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
