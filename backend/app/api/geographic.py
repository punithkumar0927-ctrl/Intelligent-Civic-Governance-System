"""
api/geographic.py — Geospatial intelligence endpoints.
"""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.issue import Issue, IssueStatus, SeverityLevel
from app.models.location import Location
from app.schemas.location_schema import (
    GeoPoint, HotspotCluster, WardReport, GeoAnalyticsResponse
)
from app.core.security import CurrentUser
from app.services.geographic_service import (
    get_geo_points, find_hotspot_clusters, ward_report, get_nearby_issues
)

router = APIRouter(prefix="/api/geographic", tags=["Geographic Intelligence"])


@router.get("/points", response_model=list[GeoPoint])
def geo_points(
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
    city: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=2000),
):
    """Return all geo-tagged issues for map rendering."""
    return get_geo_points(db, city=city, severity=severity, category=category, limit=limit)


@router.get("/hotspots", response_model=list[HotspotCluster])
def hotspots(
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
    eps_km: float = Query(0.5, description="Cluster radius in km"),
    min_samples: int = Query(3, description="Min issues to form hotspot"),
):
    """
    DBSCAN-based hotspot detection.
    Returns clusters of issues with ward, count, avg severity, centroid.
    """
    return find_hotspot_clusters(db, eps_km=eps_km, min_samples=min_samples)


@router.get("/wards", response_model=list[WardReport])
def ward_analytics(
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
    city: Optional[str] = Query(None),
):
    """Per-ward resolution stats and severity breakdown."""
    return ward_report(db, city=city)


@router.get("/nearby", response_model=list[GeoPoint])
def nearby_issues(
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(1.0, ge=0.1, le=10.0),
):
    """Find all reported issues within radius_km of given coordinate."""
    return get_nearby_issues(db, lat=lat, lon=lon, radius_km=radius_km)


@router.get("/summary", response_model=GeoAnalyticsResponse)
def geo_summary(
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
    city: Optional[str] = Query(None),
):
    """Combined geospatial analytics summary."""
    points   = get_geo_points(db, city=city, limit=2000)
    clusters = find_hotspot_clusters(db)
    wards    = ward_report(db, city=city)
    high_risk_count = (
        db.query(Issue)
        .join(Location, Location.issue_id == Issue.id)
        .filter(Location.is_high_risk_zone == True)
        .filter(Issue.status != IssueStatus.DUPLICATE)
        .count()
    )
    return GeoAnalyticsResponse(
        total_points=len(points),
        clusters=clusters,
        ward_reports=wards,
        high_risk_count=high_risk_count,
    )
