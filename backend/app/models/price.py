from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base

class CropPrice(Base):
    __tablename__ = "crop_prices"

    id = Column(Integer, primary_key=True, index=True)
    mandi_id = Column(String(255), ForeignKey("mandis.mandi_id", ondelete="CASCADE"), nullable=False, index=True)
    crop = Column(String(50), nullable=False, index=True)
    variety = Column(String(100), nullable=False)
    grade = Column(String(50), nullable=False)
    price_date = Column(Date, nullable=False, index=True)
    min_price = Column(Numeric(10, 2), nullable=False)
    max_price = Column(Numeric(10, 2), nullable=False)
    modal_price = Column(Numeric(10, 2), nullable=False)
    price_unit = Column(String(50), default="Rs./Quintal")
    created_at = Column(DateTime, server_default=func.now())

    mandi = relationship("Mandi", back_populates="prices")
