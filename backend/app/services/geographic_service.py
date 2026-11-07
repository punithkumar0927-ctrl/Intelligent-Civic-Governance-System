"""
services/geographic_service.py — Geospatial analytics for NEXUS AI.
Provides DBSCAN hotspot detection, ward-level aggregation, and proximity queries.
"""
import math
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.issue import Issue, IssueStatus, SeverityLevel
from app.models.location import Location
from app.schemas.location_schema import GeoPoint, HotspotCluster, WardReport

SEVERITY_SCORE = {"low": 0.1, "medium": 0.4, "high": 0.7, "critical": 0.95}


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def get_geo_points(
    db: Session,
    city: Optional[str] = None,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 500,
) -> list[GeoPoint]:
    query = db.query(
        Issue.id, Issue.latitude, Issue.longitude,
        Issue.severity, Issue.category, Issue.status, Issue.ward
    ).filter(
        Issue.latitude.isnot(None),
        Issue.longitude.isnot(None),
        Issue.status != IssueStatus.DUPLICATE,
    )
    if city:
        query = query.filter(Issue.city.ilike(f"%{city}%"))
    if severity:
        query = query.filter(Issue.severity == severity)
    if category:
        query = query.filter(Issue.category == category)

    rows = query.limit(limit).all()
    return [
        GeoPoint(
            id=r[0], lat=float(r[1]), lon=float(r[2]),
            severity=r[3].value if hasattr(r[3], "value") else str(r[3]),
            category=r[4].value if hasattr(r[4], "value") else str(r[4]),
            status=r[5].value if hasattr(r[5], "value") else str(r[5]),
            ward=r[6],
        )
        for r in rows
    ]


def find_hotspot_clusters(
    db: Session,
    eps_km: float = 0.5,
    min_samples: int = 3,
) -> list[HotspotCluster]:
    """
    DBSCAN-style hotspot clustering using issue coordinates.
    Returns clusters with ward label, issue count, avg severity, centroid.
    """
    points = get_geo_points(db, limit=2000)
    if len(points) < min_samples:
        return []

    coords = [(p.lat, p.lon) for p in points]
    sev_map = {p.id: SEVERITY_SCORE.get(p.severity, 0.3) for p in points}
    cat_map = {p.id: p.category for p in points}
    ward_map = {p.id: p.ward for p in points}

    visited = set()
    labels = [-1] * len(points)
    cluster_id = 0

    def region_query(idx: int) -> list[int]:
        neighbours = []
        for j, (lat2, lon2) in enumerate(coords):
            if _haversine_km(*coords[idx], lat2, lon2) <= eps_km:
                neighbours.append(j)
        return neighbours

    for i in range(len(points)):
        if i in visited:
            continue
        visited.add(i)
        neighbours = region_query(i)
        if len(neighbours) < min_samples:
            continue
        labels[i] = cluster_id
        seed_set = set(neighbours) - {i}
        queue = list(seed_set)
        while queue:
            j = queue.pop(0)
            if j not in visited:
                visited.add(j)
                jn = region_query(j)
                if len(jn) >= min_samples:
                    queue.extend(set(jn) - seed_set)
                    seed_set.update(jn)
            if labels[j] == -1:
                labels[j] = cluster_id
        cluster_id += 1

    results = []
    for cid in range(cluster_id):
        members = [i for i, l in enumerate(labels) if l == cid]
        if len(members) < min_samples:
            continue
        lats = [coords[i][0] for i in members]
        lons = [coords[i][1] for i in members]
        avg_sev = sum(sev_map[points[i].id] for i in members) / len(members)
        # Find top category
        cat_counts: dict = {}
        for i in members:
            c = cat_map[points[i].id]
            cat_counts[c] = cat_counts.get(c, 0) + 1
        top_cat = max(cat_counts, key=cat_counts.get) if cat_counts else "other"
        # Find dominant ward
        ward_list = [ward_map.get(points[i].id) for i in members if ward_map.get(points[i].id)]
        ward = max(set(ward_list), key=ward_list.count) if ward_list else "unknown"

        results.append(HotspotCluster(
            ward=ward,
            count=len(members),
            avg_severity=round(avg_sev, 3),
            top_category=top_cat,
            lat=round(sum(lats) / len(lats), 6),
            lon=round(sum(lons) / len(lons), 6),
        ))

    return sorted(results, key=lambda x: (-x.count, -x.avg_severity))[:30]


def ward_report(db: Session, city: Optional[str] = None) -> list[WardReport]:
    base = db.query(Issue).filter(Issue.ward.isnot(None))
    if city:
        base = base.filter(Issue.city.ilike(f"%{city}%"))

    wards = (
        db.query(Issue.ward, func.count(Issue.id))
        .filter(Issue.ward.isnot(None))
        .group_by(Issue.ward)
        .all()
    )

    results = []
    for ward_name, total in wards:
        q = db.query(Issue).filter(Issue.ward == ward_name)
        if city:
            q = q.filter(Issue.city.ilike(f"%{city}%"))
        resolved = q.filter(Issue.status == IssueStatus.RESOLVED).count()
        critical = q.filter(Issue.severity == SeverityLevel.CRITICAL).count()
        resolved_rows = q.filter(
            Issue.status == IssueStatus.RESOLVED,
            Issue.resolved_at.isnot(None),
        ).all()
        days = [
            (r.resolved_at - r.created_at).total_seconds() / 86400
            for r in resolved_rows if r.resolved_at and r.created_at
        ]
        avg_days = round(sum(days) / len(days), 1) if days else 0.0

        results.append(WardReport(
            ward=ward_name,
            city=city,
            total_issues=total,
            resolved=resolved,
            resolution_rate=round((resolved / total) * 100, 1) if total else 0.0,
            critical_count=critical,
            avg_resolution_days=avg_days,
        ))

    return sorted(results, key=lambda x: -x.total_issues)


def get_nearby_issues(
    db: Session, lat: float, lon: float, radius_km: float
) -> list[GeoPoint]:
    points = get_geo_points(db, limit=5000)
    return [p for p in points if _haversine_km(lat, lon, p.lat, p.lon) <= radius_km]
