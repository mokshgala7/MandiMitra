from typing import Dict, Any, Optional
from pydantic import BaseModel

class ForecastPoints(BaseModel):
    day_1: float
    day_2: float
    day_3: float

class PredictionResponse(BaseModel):
    crop: str
    mandi_id: str
    market: str
    variety: str
    grade: str
    current_price: float
    forecast: ForecastPoints
    predictions: ForecastPoints
    trend: str
    prediction_date: str
