"""Point-in-polygon lookup. PostGIS is used when the database is PostgreSQL; otherwise the same test runs in Python."""

import json
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.civic import AdministrativeBoundary

LEVEL_RANK = {
    "ulb": 5,
    "gram_panchayat": 5,
    "village": 4,
    "taluk": 3,
    "district": 2,
    "state": 1,
}


def _ring_contains(lng: float, lat: float, ring: list) -> bool:
    inside = False
    j = len(ring) - 1
    for i, point in enumerate(ring):
        xi, yi = point[0], point[1]
        xj, yj = ring[j][0], ring[j][1]
        intersects = ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-15) + xi)
        if intersects:
            inside = not inside
        j = i
    return inside


def geometry_contains(geometry: dict, lng: float, lat: float) -> bool:
    kind = geometry.get("type")
    coords = geometry.get("coordinates") or []
    if kind == "Polygon" and coords:
        if not _ring_contains(lng, lat, coords[0]):
            return False
        return not any(_ring_contains(lng, lat, hole) for hole in coords[1:])
    if kind == "MultiPolygon":
        return any(geometry_contains({"type": "Polygon", "coordinates": poly}, lng, lat) for poly in coords)
    return False


def _postgis_match(db: Session, lng: float, lat: float) -> Optional[AdministrativeBoundary]:
    if not settings.DATABASE_URL.startswith("postgres"):
        return None
    try:
        row = db.execute(
            text(
                """
                SELECT id FROM administrative_boundaries
                WHERE verified = true
                  AND geometry_json IS NOT NULL
                  AND ST_Contains(
                        ST_SetSRID(ST_GeomFromGeoJSON(geometry_json), 4326),
                        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)
                  )
                """
            ),
            {"lng": lng, "lat": lat},
        ).fetchall()
    except Exception:
        db.rollback()
        return None
    if not row:
        return None
    matches = db.query(AdministrativeBoundary).filter(AdministrativeBoundary.id.in_([item[0] for item in row])).all()
    return _choose(matches)


def _choose(matches: list[AdministrativeBoundary]) -> Optional[AdministrativeBoundary]:
    specific = [item for item in matches if item.level in {"gram_panchayat", "ulb"}]
    pool = specific or matches
    pool.sort(key=lambda item: LEVEL_RANK.get(item.level, 0), reverse=True)
    if len(pool) > 1 and LEVEL_RANK.get(pool[0].level, 0) == LEVEL_RANK.get(pool[1].level, 0):
        return None
    return pool[0] if pool else None


def locate(db: Session, lng: float, lat: float) -> Optional[AdministrativeBoundary]:
    if settings.DATABASE_URL.startswith("postgres"):
        postgis = _postgis_match(db, lng, lat)
        if postgis is not None:
            return postgis
    matches = []
    rows = db.query(AdministrativeBoundary).filter(AdministrativeBoundary.verified.is_(True)).all()
    for row in rows:
        try:
            geometry = json.loads(row.geometry_json)
        except json.JSONDecodeError:
            continue
        if geometry_contains(geometry, lng, lat):
            matches.append(row)
    return _choose(matches)


def ancestor_names(db: Session, boundary: AdministrativeBoundary) -> dict:
    names = {
        "verified_state": None,
        "verified_district": None,
        "verified_taluk": None,
        "verified_village": None,
        "verified_gram_panchayat": None,
        "verified_ulb": None,
    }
    current = boundary
    seen = set()
    while current and current.id not in seen:
        seen.add(current.id)
        field = {
            "state": "verified_state",
            "district": "verified_district",
            "taluk": "verified_taluk",
            "village": "verified_village",
            "gram_panchayat": "verified_gram_panchayat",
            "ulb": "verified_ulb",
        }.get(current.level)
        if field:
            names[field] = current.name
        current = db.query(AdministrativeBoundary).filter(AdministrativeBoundary.id == current.parent_id).first() if current.parent_id else None
    return names
