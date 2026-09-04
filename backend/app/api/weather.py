from fastapi import APIRouter, Query
from app.schemas.weather import WeatherResponse
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/api/v1/weather", tags=["Weather"])

@router.get("", response_model=WeatherResponse)
def get_weather(
    latitude: float = Query(..., description="Location latitude"),
    longitude: float = Query(..., description="Location longitude"),
    location_name: str = Query("Your Area", description="Location name for label")
):
    return WeatherService.get_weather(
        latitude=latitude,
        longitude=longitude,
        location_name=location_name
    )
