"""
ai_engine/duplicate_detection/location_similarity.py
Geographic proximity scoring for duplicate detection.
"""
import math
from typing import Optional


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def geo_similarity(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
    max_radius_km: float = 0.3,
) -> float:
    """
    Returns 0-1 proximity score.
    1.0 = same location; 0.0 = beyond max_radius_km.
    Default max radius: 300m (typical duplicate issue range).
    """
    dist = haversine_km(lat1, lon1, lat2, lon2)
    if dist >= max_radius_km:
        return 0.0
    return round(1.0 - (dist / max_radius_km), 4)


def same_ward(ward1: Optional[str], ward2: Optional[str]) -> float:
    """Returns 1.0 if same ward, 0.0 if different, 0.5 if either unknown."""
    if not ward1 or not ward2:
        return 0.5
    return 1.0 if ward1.strip().lower() == ward2.strip().lower() else 0.0


def build_location_vector(
    lat: float,
    lon: float,
    ward: Optional[str] = None,
    city: Optional[str] = None,
) -> dict:
    return {
        "lat": round(lat, 6),
        "lon": round(lon, 6),
        "ward": (ward or "").strip().lower(),
        "city": (city or "").strip().lower(),
    }


def location_score(
    loc_a: dict,
    loc_b: dict,
    max_radius_km: float = 0.3,
) -> dict:
    """
    Combined location similarity with ward + city match.
    Returns {"geo_sim", "ward_match", "city_match", "composite"}
    composite = 0.6*geo + 0.2*ward + 0.2*city
    """
    geo = geo_similarity(loc_a["lat"], loc_a["lon"], loc_b["lat"], loc_b["lon"], max_radius_km)
    w = same_ward(loc_a.get("ward"), loc_b.get("ward"))
    c = same_ward(loc_a.get("city"), loc_b.get("city"))
    composite = round(0.6 * geo + 0.2 * w + 0.2 * c, 4)
    return {"geo_sim": geo, "ward_match": w, "city_match": c, "composite": composite}
