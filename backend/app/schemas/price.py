from typing import List, Optional
from pydantic import BaseModel

class PricePoint(BaseModel):
    date: str
    price: float
    min_price: Optional[float] = None
    max_price: Optional[float] = None

class PriceHistoryResponse(BaseModel):
    crop: str
    mandi_id: Optional[str] = None
    period: str
    data_points: List[PricePoint]
