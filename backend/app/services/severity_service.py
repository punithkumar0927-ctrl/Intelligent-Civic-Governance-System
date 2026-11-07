"""
severity_service.py — ML-based severity scoring for NEXUS AI.

Model: XGBoost classifier trained on (category, image_features, description) → severity_score.
Fallback: rule-based heuristic when model file unavailable.

Features used:
  - category_encoded (one-hot or ordinal)
  - detected_label_encoded
  - confidence (YOLO)
  - edge_density, contrast, brightness, damage_area_ratio
  - description_length, keyword_hits (safety words)
  - upvotes (public urgency signal)
"""

import re
import numpy as np
from pathlib import Path
from typing import Optional

# Lazy-load model
_model = None
_scaler = None

CATEGORY_MAP = {
    "pothole":       0.7,
    "road_damage":   0.6,
    "water_leak":    0.5,
    "drainage":      0.4,
    "garbage":       0.3,
    "streetlight":   0.5,
    "sidewalk":      0.4,
    "traffic_sign":  0.5,
    "park":          0.2,
    "building":      0.8,
    "power_line":    0.9,
    "other":         0.3,
}

CRITICAL_KEYWORDS = [
    "accident", "injury", "danger", "emergency", "collapse",
    "electrocution", "flood", "fire", "fatal", "life-threatening",
    "live wire", "exposed cable", "sewage", "contamination",
]

URGENCY_KEYWORDS = [
    "urgent", "severe", "large", "deep", "broken", "cracked",
    "blocked", "overflow", "no light", "not working", "damaged",
]


def _load_model():
    global _model, _scaler
    if _model is not None:
        return _model
    try:
        import joblib
        from app.core.config import settings
        p = Path(settings.SEVERITY_MODEL_PATH)
        if p.exists():
            _model = joblib.load(p)
            print(f"[severity_service] loaded model from {p}")
        return _model
    except Exception as exc:
        print(f"[severity_service] model load failed: {exc}")
        return None


def _rule_based_score(
    category: str,
    detected_label: Optional[str],
    confidence: Optional[float],
    image_features: dict,
    description: str,
    upvotes: int,
) -> float:
    """
    Heuristic severity score (0.0–1.0) when ML model unavailable.
    Combines category risk, image signals, text keywords, and public upvotes.
    """
    score = 0.0

    # Base category risk
    cat_key = (detected_label or category or "other").lower().replace(" ", "_")
    score += CATEGORY_MAP.get(cat_key, CATEGORY_MAP.get(category.lower(), 0.3)) * 0.40

    # Image features contribution
    if image_features:
        damage_ratio = image_features.get("damage_area_ratio", 0.2)
        contrast     = image_features.get("contrast", 50) / 255.0
        is_dark      = image_features.get("is_dark", False)
        score += damage_ratio * 0.20
        score += contrast * 0.05
        if is_dark:
            score += 0.05   # nighttime = harder to see hazard

    # Detection confidence is intentionally unused. It measures box certainty, not damage severity.
    _ = confidence

    # Description keywords
    desc_lower = description.lower()
    for kw in CRITICAL_KEYWORDS:
        if kw in desc_lower:
            score += 0.20
            break
    for kw in URGENCY_KEYWORDS:
        if kw in desc_lower:
            score += 0.05

    # Upvotes signal (public urgency, capped contribution)
    score += min(upvotes / 20.0, 1.0) * 0.10

    # Description length as proxy for detail (very short = maybe low effort)
    if len(description) < 10:
        score *= 0.85

    return round(min(score, 1.0), 4)


def predict_severity(
    category: str,
    detected_label: Optional[str],
    confidence: Optional[float],
    image_features: dict,
    description: str,
    upvotes: int = 0,
) -> float:
    """
    Returns severity score 0.0 (low) to 1.0 (critical).
    Uses XGBoost if available, otherwise rule-based.
    """
    model = _load_model()

    if model is None:
        return _rule_based_score(
            category, detected_label, confidence,
            image_features, description, upvotes
        )

    try:
        # Build feature vector matching training columns
        feat = _build_feature_vector(
            category, detected_label, confidence,
            image_features, description, upvotes
        )
        score = float(model.predict_proba(feat.reshape(1, -1))[0][1])
        return round(score, 4)
    except Exception as exc:
        print(f"[severity_service] prediction error: {exc}")
        return _rule_based_score(
            category, detected_label, confidence,
            image_features, description, upvotes
        )


FEATURE_COLUMNS = [
    "cat_enc", "label_enc", "confidence",
    "edge_density", "contrast", "brightness", "damage_area_ratio",
    "texture_variance", "saturation_mean",
    "desc_len", "has_critical_kw", "has_urgency_kw",
    "upvotes", "upvotes_log",
]


def _encode_category(cat: str) -> float:
    return CATEGORY_MAP.get((cat or "other").lower(), 0.3)


def _encode_label(label: Optional[str]) -> float:
    if not label:
        return 0.0
    label_lower = label.lower()
    for k, v in CATEGORY_MAP.items():
        if k in label_lower:
            return v
    return 0.0


def _build_feature_vector(
    category, detected_label, confidence,
    image_features, description, upvotes
) -> np.ndarray:
    desc_lower = description.lower()
    has_critical = 1.0 if any(kw in desc_lower for kw in CRITICAL_KEYWORDS) else 0.0
    has_urgency  = 1.0 if any(kw in desc_lower for kw in URGENCY_KEYWORDS)  else 0.0

    feat_dict = {
        "cat_enc":           _encode_category(category),
        "label_enc":         _encode_label(detected_label),
        "confidence":        confidence or 0.0,
        "edge_density":      image_features.get("edge_density", 0.1),
        "contrast":          image_features.get("contrast", 50.0) / 255.0,
        "brightness":        image_features.get("brightness", 128.0) / 255.0,
        "damage_area_ratio": image_features.get("damage_area_ratio", 0.2),
        "texture_variance":  min(image_features.get("texture_variance", 500.0) / 5000.0, 1.0),
        "saturation_mean":   image_features.get("saturation_mean", 50.0) / 255.0,
        "desc_len":          min(len(description) / 500.0, 1.0),
        "has_critical_kw":   has_critical,
        "has_urgency_kw":    has_urgency,
        "upvotes":           min(upvotes / 50.0, 1.0),
        "upvotes_log":       np.log1p(upvotes) / np.log1p(100),
    }
    return np.array([feat_dict.get(col, 0.0) for col in FEATURE_COLUMNS], dtype=np.float32)
