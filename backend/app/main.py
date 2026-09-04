from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.api import (
    auth_router,
    mandis_router,
    prices_router,
    prediction_router,
    recommendation_router,
    search_router,
    weather_router
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure all tables exist on startup
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Database check warning: {e}")
    yield

app = FastAPI(
    title="MandiMitra API",
    description="Farmer-focused crop selling decision-support platform connecting real geography, MySQL, and ML models.",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check
@app.get("/api/v1/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "MandiMitra FastAPI Backend"}

# Include Routers
app.include_router(auth_router)
app.include_router(mandis_router)
app.include_router(prices_router)
app.include_router(prediction_router)
app.include_router(recommendation_router)
app.include_router(search_router)
app.include_router(weather_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
