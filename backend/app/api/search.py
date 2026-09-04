from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.search import SearchHistory
from app.schemas.search import SearchCreate, SearchOut
from app.services.auth_service import get_current_user_optional

router = APIRouter(prefix="/api/v1/search-history", tags=["Search History"])

@router.get("", response_model=List[SearchOut])
def get_search_history(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    query = db.query(SearchHistory)
    if current_user:
        # User-specific isolated search history
        query = query.filter(SearchHistory.user_id == current_user.id)
    else:
        # Anonymous / public recent searches
        query = query.filter(SearchHistory.user_id == None)

    # Return top 5 most recent searches
    searches = query.order_by(SearchHistory.created_at.desc()).limit(5).all()
    return [SearchOut.model_validate(s) for s in searches]

@router.post("", response_model=SearchOut, status_code=status.HTTP_201_CREATED)
def record_search(
    search_in: SearchCreate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    new_search = SearchHistory(
        user_id=current_user.id if current_user else None,
        crop=search_in.crop.lower(),
        quantity_kg=search_in.quantity_kg,
        latitude=search_in.latitude,
        longitude=search_in.longitude,
        selected_mandi_id=search_in.selected_mandi_id,
        has_middleman=search_in.has_middleman,
        middleman_price=search_in.middleman_price,
        middleman_commission=search_in.middleman_commission,
        middleman_other=search_in.middleman_other,
        recommendation=search_in.recommendation
    )
    db.add(new_search)
    db.commit()
    db.refresh(new_search)
    return SearchOut.model_validate(new_search)
