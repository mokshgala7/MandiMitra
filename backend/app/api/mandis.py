from fastapi import APIRouter, Query, HTTPException, status
from app.schemas.mandi import NearbyMandisResponse
from app.services.mandi_service import MandiService

router = APIRouter(prefix="/api/v1/mandis", tags=["Mandis"])
mandi_service = MandiService()

@router.get("/nearby", response_model=NearbyMandisResponse)
def get_nearby_mandis(
    crop: str = Query(..., description="Crop name: wheat, rice, tomato, cotton"),
    latitude: float = Query(..., description="Farmer latitude"),
    longitude: float = Query(..., description="Farmer longitude"),
    radius_km: float = Query(500.0, description="Search radius in kilometers, default 500")
):
    try:
        results = mandi_service.get_nearby_mandis(
            crop=crop.lower(),
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km
        )
        return results
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mandi search failed: {str(e)}"
        )
