from app.api.auth import router as auth_router
from app.api.mandis import router as mandis_router
from app.api.prices import router as prices_router
from app.api.prediction import router as prediction_router
from app.api.recommendation import router as recommendation_router
from app.api.search import router as search_router
from app.api.weather import router as weather_router

__all__ = [
    "auth_router",
    "mandis_router",
    "prices_router",
    "prediction_router",
    "recommendation_router",
    "search_router",
    "weather_router"
]
