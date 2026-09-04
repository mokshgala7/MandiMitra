from fastapi import APIRouter, Query, HTTPException, status
from app.schemas.prediction import PredictionResponse
from app.services.mandi_service import MandiService
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/api/v1/prediction", tags=["Prediction"])
mandi_service = MandiService()
prediction_service = PredictionService()

@router.get("", response_model=PredictionResponse)
def get_prediction(
    crop: str = Query(..., description="Crop name: wheat, rice, tomato, cotton"),
    mandi_id: str = Query(..., description="Unique mandi identifier"),
    variety: str = Query("Other", description="Crop variety, default Other"),
    grade: str = Query("FAQ", description="Crop grade, default FAQ")
):
    try:
        mandi_info = mandi_service.master_map.get(mandi_id)
        if not mandi_info:
            raise ValueError(f"Mandi ID '{mandi_id}' not found in master data.")

        market_name = mandi_info["mandi_name"]
        result = prediction_service.predict(
            crop=crop.lower(),
            market=market_name,
            variety=variety,
            grade=grade
        )
        result["mandi_id"] = mandi_id
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )
