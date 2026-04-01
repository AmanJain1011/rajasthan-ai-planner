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
