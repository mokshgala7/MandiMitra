from fastapi import APIRouter, HTTPException, status
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.mandi_service import MandiService
from app.services.prediction_service import PredictionService
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/api/v1/recommendation", tags=["Recommendation"])
mandi_service = MandiService()
prediction_service = PredictionService()
recommendation_service = RecommendationService(mandi_service, prediction_service)

@router.post("", response_model=RecommendationResponse)
def get_recommendation(request: RecommendationRequest):
    try:
        return recommendation_service.generate_recommendation(
            crop=request.crop,
            quantity_kg=request.quantity_kg,
            latitude=request.latitude,
            longitude=request.longitude,
            has_middleman=request.has_middleman,
            middleman_price=request.middleman_price,
            middleman_commission=request.middleman_commission,
            middleman_other=request.middleman_other,
            radius_km=request.radius_km
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation computation failed: {str(e)}"
        )
