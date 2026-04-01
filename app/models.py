from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.sql import func
from app.db import Base

class Place(Base):
    __tablename__ = "places"

    id = Column(String, primary_key=True, index=True)
    city = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, index=True, nullable=False)
    subcategory = Column(String, nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    opening_hours = Column(String, nullable=True)
    rating = Column(Float, nullable=True)
    rating_count = Column(Integer, nullable=True)
    price_level = Column(String, nullable=True)
    estimated_cost_min = Column(Integer, nullable=True)
    estimated_cost_max = Column(Integer, nullable=True)
    image_url = Column(String, nullable=True)
    source = Column(String, nullable=False, default="geoapify")
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
