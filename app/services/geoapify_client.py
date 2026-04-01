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
