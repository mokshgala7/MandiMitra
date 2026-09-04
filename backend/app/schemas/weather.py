from typing import Optional
from pydantic import BaseModel

class WeatherResponse(BaseModel):
    location: str
    latitude: float
    longitude: float
    temperature: float
    temperature_c: Optional[float] = None
    condition: str
    precipitation_probability: float
    precipitation_prob: Optional[float] = None
    alert: Optional[str] = None
    advisory: Optional[str] = None
    weather_code: Optional[int] = 0
    icon: str
