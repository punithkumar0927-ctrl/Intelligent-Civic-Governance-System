"""
utils/image_processor.py — OpenCV image preprocessing utilities.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional


def load_image(path: str, resize_to: Optional[tuple] = None) -> Optional[np.ndarray]:
    """Load image, optional resize. Returns BGR numpy array or None."""
    img = cv2.imread(str(path))
    if img is None:
        return None
    if resize_to:
        img = cv2.resize(img, resize_to, interpolation=cv2.INTER_AREA)
    return img


def to_grayscale(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def denoise(img: np.ndarray) -> np.ndarray:
    """Non-local means denoising for noisy phone camera photos."""
    return cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)


def enhance_contrast(img: np.ndarray) -> np.ndarray:
    """CLAHE adaptive histogram equalization."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def compute_edge_density(gray: np.ndarray, low: int = 50, high: int = 150) -> float:
    edges = cv2.Canny(gray, low, high)
    return float(np.sum(edges > 0)) / (gray.shape[0] * gray.shape[1])


def detect_damage_region(img: np.ndarray) -> dict:
    """
    Heuristic damage region detection using color segmentation.
    Looks for dark patches (potholes) and rough texture areas.
    Returns: damage_area_px, damage_ratio, confidence
    """
    gray = to_grayscale(img)
    h, w = gray.shape[:2]
    total_px = h * w

    # Dark region mask (pothole shadows)
    _, dark_mask = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)

    # Remove very dark border pixels
    dark_mask[:10, :] = 0; dark_mask[-10:, :] = 0
    dark_mask[:, :10] = 0; dark_mask[:, -10:] = 0

    dark_px = int(np.sum(dark_mask > 0))
    damage_ratio = dark_px / total_px

    return {
        "damage_area_px": dark_px,
        "damage_ratio":   round(damage_ratio, 4),
        "image_size":     [w, h],
        "confidence":     round(min(damage_ratio * 3, 1.0), 4),
    }


def resize_if_needed(path: str, max_side: int = 1920) -> str:
    """Resize image in-place if max side exceeds max_side. Returns path."""
    img = cv2.imread(path)
    if img is None:
        return path
    h, w = img.shape[:2]
    if max(h, w) <= max_side:
        return path
    scale = max_side / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    cv2.imwrite(path, resized, [cv2.IMWRITE_JPEG_QUALITY, 88])
    return path


def get_exif_gps(path: str) -> tuple[Optional[float], Optional[float]]:
    """Extract GPS from JPEG EXIF. Returns (lat, lon) or (None, None)."""
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS, GPSTAGS
        img = Image.open(path)
        exif = img._getexif()
        if not exif:
            return None, None
        gps_info = {
            GPSTAGS.get(k, k): v
            for k, v in exif.get(34853, {}).items()
        }
        if not gps_info:
            return None, None

        def _dms_to_deg(dms, ref):
            d, m, s = [float(x) for x in dms]
            deg = d + m / 60.0 + s / 3600.0
            if ref in ("S", "W"):
                deg = -deg
            return deg

        lat = _dms_to_deg(gps_info["GPSLatitude"],  gps_info.get("GPSLatitudeRef",  "N"))
        lon = _dms_to_deg(gps_info["GPSLongitude"],  gps_info.get("GPSLongitudeRef", "E"))
        return round(lat, 6), round(lon, 6)
    except Exception:
        return None, None


def strip_exif(path: str) -> str:
    """Remove all EXIF metadata (privacy). Saves in-place."""
    try:
        from PIL import Image
        img = Image.open(path)
        clean = Image.new(img.mode, img.size)
        clean.putdata(list(img.getdata()))
        clean.save(path, "JPEG", quality=88)
    except Exception as exc:
        print(f"[image_processor] strip_exif error: {exc}")
    return path
