"""
ai_engine/geographic_intelligence/location_matcher.py
Matches reported issue coordinates to known road segments and landmarks.
Uses spatial proximity + semantic label matching.
"""
import math
from typing import Optional
from dataclasses import dataclass


@dataclass
class RoadSegment:
    segment_id: str
    name: str
    lat1: float
    lon1: float
    lat2: float
    lon2: float
    road_class: str = "residential"  # primary | secondary | tertiary | residential
    surface_type: str = "asphalt"
    length_km: float = 0.0
    city: str = ""


@dataclass
class LocationMatch:
    segment_id: str
    road_name: str
    distance_m: float
    confidence: float
    nearest_point: tuple  # (lat, lon)


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _project_point_on_segment(
    plat: float, plon: float,
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> tuple[float, float]:
    """
    Approximate projection of point onto line segment using parametric formula.
    Returns (nearest_lat, nearest_lon).
    """
    dx = lon2 - lon1
    dy = lat2 - lat1
    if dx == 0 and dy == 0:
        return lat1, lon1
    t = ((plon - lon1) * dx + (plat - lat1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    proj_lat = lat1 + t * dy
    proj_lon = lon1 + t * dx
    return proj_lat, proj_lon


def match_to_road(
    lat: float,
    lon: float,
    segments: list[RoadSegment],
    max_distance_m: float = 150.0,
) -> Optional[LocationMatch]:
    """
    Find the nearest road segment within max_distance_m.
    Returns LocationMatch or None if no segment is close enough.
    """
    best: Optional[LocationMatch] = None
    best_dist = float("inf")

    for seg in segments:
        proj_lat, proj_lon = _project_point_on_segment(
            lat, lon, seg.lat1, seg.lon1, seg.lat2, seg.lon2
        )
        dist = _haversine_m(lat, lon, proj_lat, proj_lon)
        if dist < best_dist:
            best_dist = dist
            if dist <= max_distance_m:
                confidence = 1.0 - (dist / max_distance_m)
                best = LocationMatch(
                    segment_id=seg.segment_id,
                    road_name=seg.name,
                    distance_m=round(dist, 1),
                    confidence=round(confidence, 3),
                    nearest_point=(round(proj_lat, 6), round(proj_lon, 6)),
                )

    return best


def resolve_landmark(
    lat: float,
    lon: float,
    landmarks: list[dict],
    radius_m: float = 200.0,
) -> Optional[dict]:
    """
    Find the nearest named landmark (school, hospital, park, etc).
    landmarks = [{"name": str, "type": str, "lat": float, "lon": float}, ...]
    """
    nearest = None
    min_dist = float("inf")
    for lm in landmarks:
        dist = _haversine_m(lat, lon, lm["lat"], lm["lon"])
        if dist <= radius_m and dist < min_dist:
            min_dist = dist
            nearest = {**lm, "distance_m": round(dist, 1)}
    return nearest


def build_location_string(
    lat: float,
    lon: float,
    road_match: Optional[LocationMatch],
    landmark: Optional[dict],
    ward: Optional[str],
    city: Optional[str],
) -> str:
    """
    Build a human-readable location description from available data.
    """
    parts = []
    if road_match:
        parts.append(f"Near {road_match.road_name}")
    if landmark:
        parts.append(f"{landmark['type']}: {landmark['name']}")
    if ward:
        parts.append(f"Ward {ward}")
    if city:
        parts.append(city)
    if not parts:
        parts.append(f"Coordinates {lat:.4f}, {lon:.4f}")
    return " – ".join(parts)
