"""
ai_engine/geographic_intelligence/geographic_visualization.py
Generates matplotlib/Folium charts and map overlays for geographic analytics.
Produces JSON-serializable data structures consumable by the frontend.
"""
import json
from typing import Optional
from dataclasses import dataclass, asdict


@dataclass
class MapMarkerData:
    id: int
    lat: float
    lon: float
    severity: str
    category: str
    status: str
    label: str = ""
    ward: Optional[str] = None


@dataclass
class HeatmapPoint:
    lat: float
    lon: float
    weight: float  # severity × frequency


@dataclass
class ClusterBubble:
    lat: float
    lon: float
    count: int
    risk: float
    top_category: str
    label: str = ""


SEVERITY_COLORS = {
    "low": "#22c55e",
    "medium": "#f59e0b",
    "high": "#ef4444",
    "critical": "#7c3aed",
}

CATEGORY_ICONS = {
    "pothole": "🕳",
    "road_damage": "🛞",
    "garbage": "🗑",
    "streetlight": "💡",
    "drainage": "🌊",
    "waterlogging": "💧",
    "stray_animals": "🐕",
    "encroachment": "🚧",
    "other": "📍",
}


def markers_to_geojson(markers: list[MapMarkerData]) -> dict:
    """Convert marker list to GeoJSON FeatureCollection for frontend map."""
    features = []
    for m in markers:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [m.lon, m.lat],
            },
            "properties": {
                "id": m.id,
                "severity": m.severity,
                "category": m.category,
                "status": m.status,
                "label": m.label,
                "ward": m.ward,
                "color": SEVERITY_COLORS.get(m.severity, "#6b7280"),
                "icon": CATEGORY_ICONS.get(m.category, "📍"),
            },
        })
    return {"type": "FeatureCollection", "features": features}


def heatmap_data(points: list[HeatmapPoint]) -> list[list]:
    """
    Returns [[lat, lon, weight], ...] for leaflet.heat layer.
    """
    return [[p.lat, p.lon, round(p.weight, 3)] for p in points]


def cluster_overlay(clusters: list[ClusterBubble]) -> list[dict]:
    """Returns circle overlay data for Leaflet Circle layer."""
    return [
        {
            "lat": c.lat,
            "lon": c.lon,
            "count": c.count,
            "risk": c.risk,
            "radius_m": min(200 + c.count * 20, 1500),
            "color": _risk_color(c.risk),
            "top_category": c.top_category,
            "label": c.label or f"{c.count} issues – {c.top_category}",
        }
        for c in clusters
    ]


def _risk_color(risk: float) -> str:
    if risk >= 0.75:
        return "#7c3aed"   # purple = critical
    if risk >= 0.55:
        return "#ef4444"   # red = high
    if risk >= 0.35:
        return "#f59e0b"   # amber = medium
    return "#22c55e"       # green = low


def ward_summary_chart(wards: list[dict]) -> dict:
    """
    Input: [{"ward": str, "total": int, "resolved": int, "critical": int}, ...]
    Output: bar chart data for frontend AnalyticsChart component.
    """
    return {
        "labels": [w["ward"] for w in wards],
        "datasets": [
            {
                "label": "Total Issues",
                "data": [w["total"] for w in wards],
                "backgroundColor": "#3b82f6",
            },
            {
                "label": "Resolved",
                "data": [w["resolved"] for w in wards],
                "backgroundColor": "#22c55e",
            },
            {
                "label": "Critical",
                "data": [w["critical"] for w in wards],
                "backgroundColor": "#ef4444",
            },
        ],
    }


def time_series_chart(data: list[dict]) -> dict:
    """
    Input: [{"date": "2024-01-01", "count": 12}, ...]
    Output: line chart data.
    """
    return {
        "labels": [d["date"] for d in data],
        "datasets": [
            {
                "label": "Daily Reports",
                "data": [d["count"] for d in data],
                "borderColor": "#6366f1",
                "backgroundColor": "rgba(99,102,241,0.1)",
                "fill": True,
            }
        ],
    }


def generate_folium_map(
    markers: list[MapMarkerData],
    hotspots: list[ClusterBubble] = None,
    center: tuple = (12.9716, 77.5946),
    zoom: int = 12,
    title: str = "NEXUS AI – Issue Map",
) -> str:
    """
    Returns a standalone Folium HTML string for export / email reports.
    Requires folium package. Falls back to a placeholder string if unavailable.
    """
    try:
        import folium
        from folium.plugins import HeatMap, MarkerCluster

        m = folium.Map(location=list(center), zoom_start=zoom, tiles="CartoDB positron")
        folium.TileLayer("OpenStreetMap").add_to(m)

        # Marker cluster layer
        mc = MarkerCluster(name="Issues").add_to(m)
        for mk in markers:
            popup = (
                f"<b>{mk.label}</b><br>"
                f"Category: {mk.category}<br>"
                f"Severity: {mk.severity}<br>"
                f"Status: {mk.status}<br>"
                f"Ward: {mk.ward or 'N/A'}"
            )
            icon_color = SEVERITY_COLORS.get(mk.severity, "gray").lstrip("#")
            folium.Marker(
                location=[mk.lat, mk.lon],
                popup=folium.Popup(popup, max_width=250),
                tooltip=mk.label,
                icon=folium.Icon(color=icon_color, icon="exclamation-sign", prefix="fa"),
            ).add_to(mc)

        # Heatmap layer
        heat_pts = [[mk.lat, mk.lon, {"low": 1, "medium": 2, "high": 3, "critical": 5}.get(mk.severity, 1)]
                    for mk in markers]
        HeatMap(heat_pts, name="Density Heatmap", radius=18, blur=12).add_to(m)

        # Hotspot circles
        if hotspots:
            for hb in hotspots:
                radius = min(200 + hb.count * 20, 1500)
                color = _risk_color(hb.risk)
                folium.Circle(
                    location=[hb.lat, hb.lon],
                    radius=radius,
                    color=color,
                    fill=True,
                    fill_opacity=0.25,
                    popup=f"Hotspot: {hb.count} issues | Risk: {hb.risk:.2f} | {hb.top_category}",
                    tooltip=hb.label or f"{hb.count} issues",
                ).add_to(m)

        folium.LayerControl().add_to(m)
        return m._repr_html_()
    except ImportError:
        return "<!-- folium not installed: pip install folium -->"


def export_geojson_file(
    markers: list[MapMarkerData],
    hotspots: list[ClusterBubble],
    filepath: str = "storage/nexus_map.geojson",
) -> str:
    """Write combined GeoJSON to file; returns path."""
    layer_markers = markers_to_geojson(markers)
    layer_hotspots = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [hb.lon, hb.lat]},
                "properties": asdict(hb),
            }
            for hb in (hotspots or [])
        ],
    }
    combined = {
        "type": "FeatureCollection",
        "metadata": {"markers": len(markers), "hotspots": len(hotspots or [])},
        "layers": [layer_markers, layer_hotspots],
    }
    with open(filepath, "w") as f:
        json.dump(combined, f, indent=2)
    return filepath
