from sqlalchemy import Column, Integer, String, Numeric, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class Mandi(Base):
    __tablename__ = "mandis"

    id = Column(Integer, primary_key=True, index=True)
    mandi_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    district = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
    latitude = Column(Numeric(10, 6), nullable=False)
    longitude = Column(Numeric(10, 6), nullable=False)
    geocoding_source = Column(String(50), default="osm_nominatim")
    geocoding_confidence = Column(String(50), default="verified")
    created_at = Column(DateTime, server_default=func.now())

    prices = relationship("CropPrice", back_populates="mandi", cascade="all, delete-orphan")
