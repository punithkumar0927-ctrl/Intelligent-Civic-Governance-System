"""
ai_engine/geographic_intelligence/hotspot_analysis.py
Hotspot detection, trend analysis, and risk scoring for geographic clusters.
"""
import math
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class IssuePoint:
    issue_id: int
    lat: float
    lon: float
    severity: str       # low | medium | high | critical
    category: str       # pothole | garbage | streetlight | drainage | road_damage
    status: str         # open | in_progress | resolved | duplicate
    created_at: datetime
    reported_count: int = 1  # aggregated duplicates


@dataclass
class Hotspot:
    hotspot_id: str
    centroid_lat: float
    centroid_lon: float
    radius_km: float
    issue_count: int
    categories: dict = field(default_factory=dict)
    severity_breakdown: dict = field(default_factory=dict)
    risk_score: float = 0.0      # 0-1 composite
    trend: str = "stable"        # increasing | stable | decreasing
    ward: Optional[str] = None
    top_category: str = ""
    resolved_rate: float = 0.0
    days_since_last_resolution: Optional[int] = None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


SEVERITY_WEIGHTS = {"low": 0.15, "medium": 0.35, "high": 0.65, "critical": 0.95}


def compute_risk_score(
    avg_severity: float,
    density_per_km2: float,
    unresolved_ratio: float,
    days_stale: float,
    nearby_high_risk: bool = False,
) -> float:
    """
    Composite hotspot risk score (0–1).
    - avg_severity: mean severity weight 0-1
    - density_per_km2: issues per sq km
    - unresolved_ratio: fraction still open (0-1)
    - days_stale: avg days since created for open issues
    - nearby_high_risk: True if near school/hospital (adds 0.1)
    """
    sev_score = avg_severity
    density_score = min(density_per_km2 / 50.0, 1.0)  # saturates at 50/km²
    backlog_score = unresolved_ratio
    stale_score = min(days_stale / 30.0, 1.0)          # saturates at 30 days
    bonus = 0.10 if nearby_high_risk else 0.0

    score = (
        0.30 * sev_score +
        0.25 * density_score +
        0.25 * backlog_score +
        0.20 * stale_score +
        bonus
    )
    return round(min(score, 1.0), 4)


def detect_trend(
    points: list[IssuePoint],
    window_days: int = 30,
) -> str:
    """
    Compare issue count in recent window vs prior window.
    Returns 'increasing', 'stable', or 'decreasing'.
    """
    if not points:
        return "stable"
    now = max(p.created_at for p in points)
    cutoff_recent = now - timedelta(days=window_days)
    cutoff_prior = cutoff_recent - timedelta(days=window_days)

    recent = sum(1 for p in points if p.created_at >= cutoff_recent)
    prior = sum(1 for p in points if cutoff_prior <= p.created_at < cutoff_recent)

    if prior == 0 and recent == 0:
        return "stable"
    if prior == 0 and recent > 0:
        return "increasing"
    ratio = recent / prior
    if ratio > 1.2:
        return "increasing"
    elif ratio < 0.8:
        return "decreasing"
    return "stable"


def find_hotspots(
    points: list[IssuePoint],
    eps_km: float = 0.4,
    min_pts: int = 4,
    nearby_high_risk: bool = False,
) -> list[Hotspot]:
    """
    Grid-based hotspot detection (lightweight DBSCAN alternative for large sets).
    Returns sorted list of Hotspot objects by risk_score descending.
    """
    if len(points) < min_pts:
        return []

    # Grid partition (rough 100m cells)
    grid: dict = {}
    cell_deg = eps_km / 111.0  # approx degrees per cell

    for p in points:
        key = (round(p.lat / cell_deg), round(p.lon / cell_deg))
        grid.setdefault(key, []).append(p)

    hotspots = []
    hotspot_idx = 0

    for key, cell_points in grid.items():
        # Expand: check 8 neighbors
        all_pts = list(cell_points)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if (di, dj) == (0, 0):
                    continue
                nk = (key[0] + di, key[1] + dj)
                all_pts.extend(grid.get(nk, []))

        if len(all_pts) < min_pts:
            continue

        # Deduplicate by issue_id
        seen_ids = {}
        for p in all_pts:
            seen_ids[p.issue_id] = p
        unique_pts = list(seen_ids.values())

        # Filter to within eps_km of centroid
        clat = sum(p.lat for p in unique_pts) / len(unique_pts)
        clon = sum(p.lon for p in unique_pts) / len(unique_pts)
        in_radius = [p for p in unique_pts if _haversine_km(clat, clon, p.lat, p.lon) <= eps_km * 2]

        if len(in_radius) < min_pts:
            continue

        # Severity
        sev_vals = [SEVERITY_WEIGHTS.get(p.severity, 0.2) for p in in_radius]
        avg_sev = sum(sev_vals) / len(sev_vals)
        sev_breakdown: dict = {}
        for p in in_radius:
            sev_breakdown[p.severity] = sev_breakdown.get(p.severity, 0) + 1

        # Categories
        cat_counts: dict = {}
        for p in in_radius:
            cat_counts[p.category] = cat_counts.get(p.category, 0) + 1
        top_cat = max(cat_counts, key=cat_counts.get)

        # Unresolved ratio
        open_count = sum(1 for p in in_radius if p.status in ("open", "in_progress"))
        resolved_count = sum(1 for p in in_radius if p.status == "resolved")
        unresolved_ratio = open_count / len(in_radius) if in_radius else 0.0
        resolved_rate = resolved_count / len(in_radius) if in_radius else 0.0

        # Days stale
        now = datetime.utcnow()
        open_pts = [p for p in in_radius if p.status in ("open", "in_progress")]
        days_stale = (
            sum((now - p.created_at).days for p in open_pts) / len(open_pts)
            if open_pts else 0.0
        )

        # Density
        area_km2 = math.pi * (eps_km * 2) ** 2
        density = len(in_radius) / area_km2 if area_km2 > 0 else 0

        risk = compute_risk_score(avg_sev, density, unresolved_ratio, days_stale, nearby_high_risk)
        trend = detect_trend(in_radius)

        hotspot_idx += 1
        hotspots.append(Hotspot(
            hotspot_id=f"HS-{hotspot_idx:04d}",
            centroid_lat=round(clat, 6),
            centroid_lon=round(clon, 6),
            radius_km=eps_km * 2,
            issue_count=len(in_radius),
            categories=cat_counts,
            severity_breakdown=sev_breakdown,
            risk_score=risk,
            trend=trend,
            top_category=top_cat,
            resolved_rate=round(resolved_rate, 3),
            days_since_last_resolution=int(days_stale) if open_pts else None,
        ))

    return sorted(hotspots, key=lambda x: -x.risk_score)[:50]
