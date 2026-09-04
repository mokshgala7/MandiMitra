from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.price import PriceHistoryResponse
from app.services.price_service import PriceService

router = APIRouter(prefix="/api/v1/prices", tags=["Prices"])

@router.get("/history", response_model=PriceHistoryResponse)
def get_price_history(
    crop: str = Query(..., description="Crop name: wheat, rice, tomato, cotton"),
    mandi_id: Optional[str] = Query(None, description="Optional specific mandi ID"),
    period: str = Query("YTD", description="1D, 1W, 3W, 1M, 6M, YTD"),
    db: Session = Depends(get_db)
):
    valid_periods = ["1D", "1W", "3W", "1M", "6M", "YTD"]
    if period.upper() not in valid_periods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period '{period}'. Supported periods: {valid_periods}"
        )

    data_points = PriceService.get_price_history(
        db=db,
        crop=crop,
        mandi_id=mandi_id,
        period=period.upper()
    )

    return PriceHistoryResponse(
        crop=crop.lower(),
        mandi_id=mandi_id,
        period=period.upper(),
        data_points=data_points
    )
