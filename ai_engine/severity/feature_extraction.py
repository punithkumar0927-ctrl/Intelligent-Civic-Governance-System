"""
ai_engine/severity/feature_extraction.py
Extracts tabular features from images + metadata for XGBoost severity prediction.
"""
import cv2
import numpy as np
from typing import Optional
from dataclasses import dataclass


@dataclass
class SeverityFeatures:
    edge_density: float       # Canny edges / total pixels
    dark_ratio: float         # fraction pixels < 60 gray
    texture_variance: float   # std deviation of grayscale
    damage_area_pct: float    # damage bbox area / image area
    bbox_count: int           # detected damage regions
    mean_confidence: float    # avg YOLO confidence
    brightness_mean: float    # mean gray value (0-255)
    contrast_range: int       # p95 - p5 of gray values
    aspect_ratio: float       # avg bbox width/height
    weather: int = 0          # 0=clear 1=rain 2=fog (from filename/meta)
    road_type: int = 0        # 0=residential 1=arterial 2/highway
    traffic_level: int = 0    # 0=low 1=medium 2=high
    image_area_megapixels: float = 0.41


def canny_edges(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Canny(gray, 50, 150)


def extract_features(
    image_path: str,
    detections: list[dict] = None,  # [{"bbox": (x1,y1,x2,y2), "conf": float}]
    metadata: dict = None,
) -> SeverityFeatures:
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(image_path)
    img = cv2.resize(img, (640, 640))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    total_px = h * w

    edges = canny_edges(img)
    edge_density = float(np.mean(edges > 0))
    dark_ratio = float(np.mean(gray < 60))
    texture_var = float(np.std(gray)) / 255.0
    brightness = float(np.mean(gray))
    p5, p95 = np.percentile(gray, [5, 95])
    contrast_range = int(p95 - p5)

    detections = detections or []
    bbox_count = len(detections)
    mean_conf = float(np.mean([d["conf"] for d in detections])) if detections else 0.0
    damage_area = 0.0
    aspect_sum = 0.0
    for d in detections:
        x1, y1, x2, y2 = d["bbox"]
        area = max(0, (x2 - x1)) * max(0, (y2 - y1))
        damage_area += area
        if (y2 - y1) > 0:
            aspect_sum += (x2 - x1) / (y2 - y1)
    damage_area_pct = damage_area / total_px
    aspect_ratio = aspect_sum / bbox_count if bbox_count else 0.0

    meta = metadata or {}
    return SeverityFeatures(
        edge_density=round(edge_density, 4),
        dark_ratio=round(dark_ratio, 4),
        texture_variance=round(texture_var, 4),
        damage_area_pct=round(damage_area_pct, 4),
        bbox_count=bbox_count,
        mean_confidence=round(mean_conf, 4),
        brightness_mean=round(brightness, 2),
        contrast_range=contrast_range,
        aspect_ratio=round(aspect_ratio, 3),
        weather=meta.get("weather", 0),
        road_type=meta.get("road_type", 0),
        traffic_level=meta.get("traffic_level", 0),
        image_area_megapixels=round(total_px / 1e6, 3),
    )


def to_numpy(feat: SeverityFeatures) -> np.ndarray:
    return np.array([
        feat.edge_density, feat.dark_ratio, feat.texture_variance,
        feat.damage_area_pct, feat.bbox_count, feat.mean_confidence,
        feat.brightness_mean, feat.contrast_range, feat.aspect_ratio,
        feat.weather, feat.road_type, feat.traffic_level,
        feat.image_area_megapixels,
    ], dtype=np.float32)


FEATURE_NAMES = [
    "edge_density", "dark_ratio", "texture_variance",
    "damage_area_pct", "bbox_count", "mean_confidence",
    "brightness_mean", "contrast_range", "aspect_ratio",
    "weather", "road_type", "traffic_level",
    "image_area_megapixels",
]
