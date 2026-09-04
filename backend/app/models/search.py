from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, func
from app.database import Base

class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    crop = Column(String(50), nullable=False)
    quantity_kg = Column(Numeric(10, 2), nullable=False)
    latitude = Column(Numeric(10, 6), nullable=False)
    longitude = Column(Numeric(10, 6), nullable=False)
    selected_mandi_id = Column(String(255), nullable=True)
    has_middleman = Column(Boolean, default=False)
    middleman_price = Column(Numeric(10, 2), nullable=True)
    middleman_commission = Column(Numeric(10, 2), nullable=True)
    middleman_other = Column(Numeric(10, 2), nullable=True)
    recommendation = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
