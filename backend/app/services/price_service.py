from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.price import CropPrice

class PriceService:
    @staticmethod
    def get_price_history(db: Session, crop: str, mandi_id: Optional[str] = None, period: str = "YTD") -> List[Dict[str, Any]]:
        crop_clean = crop.strip().lower()
        query = db.query(
            CropPrice.price_date,
            func.avg(CropPrice.modal_price).label("avg_modal"),
            func.min(CropPrice.min_price).label("min_price"),
            func.max(CropPrice.max_price).label("max_price")
        ).filter(CropPrice.crop == crop_clean)

        if mandi_id:
            query = query.filter(CropPrice.mandi_id == mandi_id)

        # Determine latest date available in dataset
        latest_date_record = db.query(func.max(CropPrice.price_date)).filter(CropPrice.crop == crop_clean).scalar()
        if not latest_date_record:
            return []

        latest_date = latest_date_record

        period_upper = period.upper()
        if period_upper == "1D":
            start_date = latest_date - timedelta(days=1)
        elif period_upper == "1W":
            start_date = latest_date - timedelta(days=7)
        elif period_upper == "3W":
            start_date = latest_date - timedelta(days=21)
        elif period_upper == "1M":
            start_date = latest_date - timedelta(days=30)
        elif period_upper == "6M":
            start_date = latest_date - timedelta(days=180)
        elif period_upper == "YTD":
            # Start of the year of latest date
            start_date = datetime(latest_date.year, 1, 1).date()
        else:
            start_date = latest_date - timedelta(days=365)

        records = query.filter(CropPrice.price_date >= start_date)\
                       .group_by(CropPrice.price_date)\
                       .order_by(CropPrice.price_date.asc())\
                       .all()

        results = []
        for r in records:
            results.append({
                "date": r.price_date.strftime("%d-%m-%Y"),
                "price": round(float(r.avg_modal), 2),
                "min_price": round(float(r.min_price), 2),
                "max_price": round(float(r.max_price), 2),
            })
        return results
