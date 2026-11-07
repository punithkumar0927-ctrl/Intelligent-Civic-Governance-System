"""Transparent severity baseline. Detection confidence is not treated as severity."""

from typing import Optional

CATEGORY_RISK = {
    "pothole": 0.55,
    "d40": 0.55,
    "road_damage": 0.45,
    "d00": 0.40,
    "d10": 0.40,
    "d20": 0.60,
    "water_leak": 0.50,
    "drainage": 0.40,
    "garbage": 0.25,
    "streetlight": 0.35,
    "sidewalk": 0.30,
    "other": 0.20,
}


def rule_severity(
    category: str,
    damaged_area_ratio: float = 0.0,
    region_count: int = 0,
    road_type: Optional[str] = None,
    description: str = "",
) -> dict:
    """
    Return LOW/MEDIUM/HIGH/CRITICAL from observable report features.

    This is a baseline, not a measurement of pothole depth or crash risk.
    """
    key = (category or "other").lower().replace(" ", "_")
    score = CATEGORY_RISK.get(key, 0.20)
    area = max(0.0, min(float(damaged_area_ratio or 0.0), 1.0))
    score += area * 0.25
    score += min(max(region_count, 0), 5) * 0.04
    if (road_type or "").lower() in {"arterial", "highway", "primary"}:
        score += 0.08
    text = (description or "").lower()
    if any(word in text for word in ("collapse", "injury", "live wire", "flood")):
        score += 0.15
    score = round(min(score, 1.0), 4)
    if score >= 0.75:
        level = "CRITICAL"
    elif score >= 0.50:
        level = "HIGH"
    elif score >= 0.25:
        level = "MEDIUM"
    else:
        level = "LOW"
    return {
        "level": level,
        "score": score,
        "model_version": "severity-rules-1",
        "contributing_features": {
            "category": key,
            "damaged_area_ratio": area,
            "region_count": region_count,
            "road_type": road_type,
        },
        "human_review_status": "pending",
        "limitation": "Ordinary photographs do not measure physical depth or official road-safety risk.",
    }
