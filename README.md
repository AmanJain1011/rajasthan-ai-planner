# Rajasthan AI Planner (Phase 1)

## Setup (Windows)
1. Create virtual env:
   - `python -m venv .venv`
   - `.venv\Scripts\activate`
2. Install deps:
   - `pip install -r requirements.txt`
3. Create `.env` from `.env.example` and add your Geoapify key.
4. Run API:
   - `uvicorn app.main:app --reload`
5. Open docs:
   - http://127.0.0.1:8000/docs

## First test
- POST `/api/refresh?city=Jaipur&category=food`
- GET `/api/map?city=Jaipur&categories=food,temples,museums`

Create a new file .env.example with the following content:
DATABASE_URL=sqlite:///./travel_planner.db
GEOAPIFY_API_KEY=PASTE_YOUR_GEOAPIFY_KEY

Create a new file app/db.py with the following content:
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./travel_planner.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Create a new file app/constants.py with the following content:
CITIES = ["Jaipur", "Jodhpur", "Bikaner", "Ajmer", "Udaipur", "Pushkar", "Jaisalmer"]

CATEGORY_MAP = {
    "attractions": ["tourism.sights", "entertainment"],
    "food": ["catering.restaurant", "catering.fast_food", "catering.cafe"],
    "parks": ["leisure.park"],
    "temples": ["religion"],
    "museums": ["entertainment.museum"],
    "hotels": ["accommodation.hotel", "accommodation.guest_house", "accommodation.hostel"]
}

Create a new file app/models.py with the following content:
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

Create a new file app/schemas.py with the following content:
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

Create a new file app/services/geoapify_client.py with the following content:
import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEOAPIFY_API_KEY", "")
BASE_URL = "https://api.geoapify.com/v2/places"

def fetch_places(city: str, categories: list[str], limit: int = 50):
    params = {
        "categories": ",".join(categories),
        "filter": f"city:{city}",
        "limit": limit,
        "apiKey": API_KEY
    }
    r = requests.get(BASE_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("features", [])

def normalize_feature(feature: dict, city: str, root_category: str):
    props = feature.get("properties", {})
    lat = props.get("lat")
    lon = props.get("lon")
    if lat is None or lon is None:
        return None

    source_id = props.get("place_id") or props.get("name", "unknown")
    _id = f"{city.lower()}::{root_category}::{source_id}"

    return {
        "id": _id,
        "city": city,
        "name": props.get("name", "Unknown"),
        "category": root_category,
        "subcategory": props.get("categories", [None])[0] if props.get("categories") else None,
        "lat": float(lat),
        "lon": float(lon),
        "address": props.get("formatted"),
        "phone": None,
        "website": props.get("website"),
        "opening_hours": props.get("opening_hours"),
        "rating": None,
        "rating_count": None,
        "price_level": None,
        "estimated_cost_min": None,
        "estimated_cost_max": None,
        "image_url": None,
        "source": "geoapify"
    }

Create a new file app/routes/places.py with the following content:
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Place
from app.schemas import PlaceOut
from app.constants import CITIES, CATEGORY_MAP
from app.services.geoapify_client import fetch_places, normalize_feature

router = APIRouter(tags=["places"])

@router.get("/cities")
def get_cities():
    return {"cities": CITIES}

@router.post("/refresh")
def refresh_city_category(
    city: str = Query(...),
    category: str = Query(...),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    if city not in CITIES:
        raise HTTPException(status_code=400, detail="Unsupported city")
    if category not in CATEGORY_MAP:
        raise HTTPException(status_code=400, detail="Unsupported category")

    features = fetch_places(city=city, categories=CATEGORY_MAP[category], limit=limit)
    upserted = 0

    for f in features:
        data = normalize_feature(f, city=city, root_category=category)
        if not data:
            continue

        row = db.query(Place).filter(Place.id == data["id"]).first()
        if row:
            for k, v in data.items():
                setattr(row, k, v)
        else:
            db.add(Place(**data))
        upserted += 1

    db.commit()
    return {"city": city, "category": category, "fetched": len(features), "upserted": upserted}

@router.get("/places", response_model=list[PlaceOut])
def list_places(city: str, category: str, db: Session = Depends(get_db)):
    return db.query(Place).filter(Place.city == city, Place.category == category).all()

@router.get("/map")
def map_data(city: str, categories: str, db: Session = Depends(get_db)):
    cat_list = [c.strip() for c in categories.split(",") if c.strip()]
    rows = db.query(Place).filter(Place.city == city, Place.category.in_(cat_list)).all()
    return {
        "city": city,
        "count": len(rows),
        "markers": [
            {
                "id": r.id,
                "name": r.name,
                "category": r.category,
                "lat": r.lat,
                "lon": r.lon,
                "address": r.address,
                "opening_hours": r.opening_hours,
                "phone": r.phone,
                "image_url": r.image_url
            } for r in rows
        ]
    }

Create a new file app/main.py with the following content:
from fastapi import FastAPI
from app.db import Base, engine
from app.routes.places import router as places_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rajasthan AI Planner", version="0.1.0")
app.include_router(places_router, prefix="/api")

Create a new file map.html with the following content:
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Rajasthan Map</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
  <style>#map{height:100vh;} .top{position:absolute;z-index:1000;background:#fff;padding:8px;left:10px;top:10px;border-radius:8px;}</style>
</head>
<body>
  <div class="top">
    <select id="city">
      <option>Jaipur</option><option>Jodhpur</option><option>Bikaner</option>
      <option>Ajmer</option><option>Udaipur</option><option>Pushkar</option><option>Jaisalmer</option>
    </select>
    <button onclick="loadMap()">Load</button>
  </div>
  <div id="map"></div>
  <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
  <script>
    const map = L.map('map').setView([26.9124,75.7873], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19}).addTo(map);
    let layerGroup = L.layerGroup().addTo(map);

    async function loadMap(){
      const city = document.getElementById('city').value;
      const url = `http://127.0.0.1:8000/api/map?city=${city}&categories=food,temples,museums,parks,attractions,hotels`;
      const res = await fetch(url);
      const data = await res.json();

      layerGroup.clearLayers();
      data.markers.forEach(m=>{
        const marker = L.marker([m.lat,m.lon]).addTo(layerGroup);
        marker.bindPopup(`<b>${m.name}</b><br/>${m.category}<br/>${m.address || ''}<br/>${m.opening_hours || ''}`);
      });

      if(data.markers.length){
        map.setView([data.markers[0].lat,data.markers[0].lon], 12);
      }
    }
  </script>
</body>
</html>
