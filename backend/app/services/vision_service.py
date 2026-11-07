"""
vision_service.py — Computer Vision pipeline for NEXUS AI.

Architecture:
  Image → OpenCV preprocessing → YOLOv8 inference → Post-processing → Results

Primary model: YOLOv8n (nano, CPU-friendly) fine-tuned on road-damage datasets.
Fallback: If custom model unavailable, uses YOLOv8 pre-trained (COCO 80 classes)
with heuristic mapping to infrastructure categories.
"""

import hashlib
from pathlib import Path
from typing import Optional

try:
    import cv2
    _CV2_OK = True
except ImportError:
    _CV2_OK = False

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

# Lazy-load a road-damage checkpoint only. COCO weights are never substituted.
_model = None
_model_path = None

NOT_CONFIGURED_MESSAGE = (
    "MODEL_NOT_CONFIGURED: no trained road-damage weights are registered. "
    "Train on RDD2022 (D00, D10, D20, D40) and set YOLO_MODEL_PATH to best.pt. "
    "Detections are not invented."
)


def _get_model():
    global _model, _model_path
    if _model is not None:
        return _model
    try:
        import sys
        root = Path(__file__).resolve().parents[3]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from ai_engine.detection.model_loader import load_yolo
        model, path = load_yolo()
        _model = model
        _model_path = path
        return _model
    except Exception as exc:
        print(f"[vision_service] model load error: {exc}")
        return None


def compute_phash(image_path: str, hash_size: int = 16) -> str:
    """
    Compute perceptual hash (dHash) for duplicate image detection.
    Robust to small resizes, color changes, and JPEG compression.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return ""
    # Resize to hash_size x (hash_size+1)
    img = cv2.resize(img, (hash_size, hash_size + 1), interpolation=cv2.INTER_AREA)
    # Compute gradient
    diff = img[1:] > img[:-1]
    # Convert to hex string
    flat = diff.flatten()
    as_int = int("".join("1" if x else "0" for x in flat), 2)
    return format(as_int, f"0{hash_size * hash_size // 4}x")


def hamming_distance(h1: str, h2: str) -> int:
    """Returns number of differing bits between two hex hashes."""
    if not h1 or not h2:
        return 999
    try:
        x = int(h1, 16) ^ int(h2, 16)
        return bin(x).count("1")
    except Exception:
        return 999


def compute_image_features(image_path: str) -> dict:
    """
    Extract quantitative features for the severity model.
    Returns: brightness, contrast, edge_density, color_dominance, texture_variance
    """
    img = cv2.imread(image_path)
    if img is None:
        return {}

    gray  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv   = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Basic stats
    h, w = gray.shape[:2]
    brightness     = float(np.mean(gray))
    contrast       = float(np.std(gray))
    edge_img       = cv2.Canny(gray, 50, 150)
    edge_density   = float(np.sum(edge_img > 0)) / (h * w)
    texture_var    = float(np.var(gray))
    saturation     = float(np.mean(hsv[:, :, 1]))
    damage_area_ratio = float(edge_density * 4)  # heuristic proxy for damage region

    # Color dominance (brownish/grey = road; greenish = vegetation; colorful = garbage)
    r_mean = float(np.mean(img[:, :, 2]))
    g_mean = float(np.mean(img[:, :, 1]))
    b_mean = float(np.mean(img[:, :, 0]))

    return {
        "width":             w,
        "height":            h,
        "brightness":        brightness,
        "contrast":          contrast,
        "edge_density":      edge_density,
        "texture_variance":  texture_var,
        "saturation_mean":   saturation,
        "damage_area_ratio": min(damage_area_ratio, 1.0),
        "r_mean":            r_mean,
        "g_mean":            g_mean,
        "b_mean":            b_mean,
        "is_dark":           brightness < 60,
        "is_noisy":          texture_var > 1000,
    }


def detect_issue(image_path: str) -> Optional[dict]:
    """
    Run YOLOv8 inference on the image.
    Returns: {"top_label": str, "max_confidence": float, "detections": [...], "phash": str}
    """
    model = _get_model()
    phash = compute_phash(image_path) if _CV2_OK else ""

    if model is None:
        return {
            "status": "MODEL_NOT_CONFIGURED",
            "top_label": None,
            "max_confidence": 0.0,
            "detections": [],
            "phash": phash,
            "message": NOT_CONFIGURED_MESSAGE,
        }

    try:
        results = model.predict(
            source=image_path,
            conf=0.25,
            iou=0.45,
            verbose=False,
            device="cpu",   # CPU for MVP — switch to 0 for GPU
        )

        detections = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls_id  = int(box.cls[0])
                conf    = float(box.conf[0])
                label   = model.names[cls_id] if hasattr(model, "names") else str(cls_id)
                xyxy = box.xyxy[0].tolist()
                detections.append({
                    "class": label,
                    "class_id": cls_id,
                    "label": label,
                    "raw_label": label,
                    "confidence": conf,
                    "bounding_box": {
                        "x1": xyxy[0], "y1": xyxy[1], "x2": xyxy[2], "y2": xyxy[3],
                    },
                    "bbox": xyxy,
                })

        if not detections:
            return {
                "status": "completed",
                "top_label": None,
                "max_confidence": 0.0,
                "detections": [],
                "phash": phash,
                "model_path": str(_model_path) if _model_path else None,
            }

        detections.sort(key=lambda x: x["confidence"], reverse=True)
        best = detections[0]

        return {
            "status": "completed",
            "top_label": best["label"],
            "max_confidence": best["confidence"],
            "detections": detections,
            "phash": phash,
            "img_shape": list(results[0].orig_shape),
            "model_path": str(_model_path) if _model_path else None,
        }

    except Exception as exc:
        print(f"[vision_service] inference error: {exc}")
        return {
            "status": "error",
            "top_label": None,
            "max_confidence": 0.0,
            "detections": [],
            "phash": phash,
            "error": str(exc),
            "message": "Detection failed. No result was invented.",
        }


def compare_images(before_path: str, after_path: str) -> dict:
    """
    Before/After structural comparison for resolution verification.
    Uses SSIM-style edge comparison + brightness delta.
    """
    img_b = cv2.imread(before_path)
    img_a = cv2.imread(after_path)

    if img_b is None or img_a is None:
        return {"error": "One or both images unreadable"}

    # Resize to common size for comparison
    h, w = 512, 512
    img_b = cv2.resize(img_b, (w, h))
    img_a = cv2.resize(img_a, (w, h))

    gray_b = cv2.cvtColor(img_b, cv2.COLOR_BGR2GRAY)
    gray_a = cv2.cvtColor(img_a, cv2.COLOR_BGR2GRAY)

    edge_b = cv2.Canny(gray_b, 50, 150)
    edge_a = cv2.Canny(gray_a, 50, 150)

    edge_density_b = float(np.sum(edge_b > 0)) / (w * h)
    edge_density_a = float(np.sum(edge_a > 0)) / (w * h)

    brightness_b = float(np.mean(gray_b))
    brightness_a = float(np.mean(gray_a))

    # Structural Similarity (simplified)
    from skimage.metrics import structural_similarity as ssim
    try:
        ssim_score = float(ssim(gray_b, gray_a))
    except Exception:
        ssim_score = 0.5

    edge_reduction = max(0.0, edge_density_b - edge_density_a) / max(edge_density_b, 0.01)

    resolved_prob = min(1.0, max(0.0,
        0.4 * ssim_score +
        0.35 * edge_reduction +
        0.25 * (1.0 - abs(brightness_b - brightness_a) / 255.0)
    ))

    return {
        "ssim_score":       round(ssim_score, 4),
        "edge_density_before": round(edge_density_b, 4),
        "edge_density_after":  round(edge_density_a, 4),
        "edge_reduction":   round(edge_reduction, 4),
        "brightness_delta": round(abs(brightness_b - brightness_a), 2),
        "resolved_probability": round(resolved_prob, 4),
        "recommendation":   "Likely resolved" if resolved_prob > 0.65 else
                            "Possibly resolved — manual review needed" if resolved_prob > 0.40 else
                            "Issue likely still present",
    }
