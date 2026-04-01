from pydantic import BaseModel
from typing import Optional

class PlaceOut(BaseModel):
    id: str
    city: str
    name: str
    category: str
    subcategory: Optional[str] = None
    lat: float
    lon: float
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[str] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    price_level: Optional[str] = None
    estimated_cost_min: Optional[int] = None
    estimated_cost_max: Optional[int] = None
    image_url: Optional[str] = None
    source: str

    class Config:
        from_attributes = True
