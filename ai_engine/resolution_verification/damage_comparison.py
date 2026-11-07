"""
ai_engine/resolution_verification/damage_comparison.py
Pixel-level and feature-level comparison of before/after damage images.
"""
import cv2
import numpy as np
from typing import Optional


def edge_density(img: np.ndarray) -> float:
    """
    Canny edge density (fraction of edge pixels) as damage proxy.
    Returns 0-1.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    edges = cv2.Canny(gray, 50, 150)
    return float(np.mean(edges > 0))


def damage_score(img: np.ndarray) -> float:
    """
    Composite damage score from edge density + texture variance + dark-pixel ratio.
    Higher = more damage visible.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    ed = edge_density(img)
    tv = float(np.std(gray)) / 255.0
    dark = float(np.mean(gray < 60))
    return round(0.4 * ed + 0.35 * tv + 0.25 * dark, 4)


def pixel_diff(before: np.ndarray, after: np.ndarray) -> dict:
    """
    Absolute pixel difference statistics.
    Returns {"mean_diff", "max_diff", "pct_changed"}.
    """
    if before.shape != after.shape:
        after = cv2.resize(after, (before.shape[1], before.shape[0]))
    diff = cv2.absdiff(before, after)
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY) if len(diff.shape) == 3 else diff
    return {
        "mean_diff": round(float(np.mean(gray_diff)), 2),
        "max_diff": int(np.max(gray_diff)),
        "pct_changed": round(float(np.mean(gray_diff > 30)) * 100, 2),
    }


def ssim_single(before: np.ndarray, after: np.ndarray) -> float:
    """
    Structural Similarity Index between two same-sized BGR images.
    Returns value in [0, 1]. Falls back to correlation if skimage unavailable.
    """
    if before.shape != after.shape:
        after = cv2.resize(after, (before.shape[1], before.shape[0]))

    try:
        from skimage.metrics import structural_similarity as ssim
        gb = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
        ga = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)
        score, _ = ssim(gb, ga, full=True)
        return round(float(score), 4)
    except ImportError:
        gb = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY).astype(float).flatten()
        ga = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY).astype(float).flatten()
        corr = np.corrcoef(gb, ga)[0, 1]
        return round(float(corr), 4)


def region_comparison(
    before: np.ndarray,
    after: np.ndarray,
    damage_bbox: Optional[tuple] = None,  # (x1,y1,x2,y2) normalised
) -> dict:
    """
    Compare only the damage region (or full image if bbox is None).
    Returns {"edge_before", "edge_after", "edge_reduction_pct",
             "damage_before", "damage_after", "damage_reduction_pct"}.
    """
    if damage_bbox:
        h, w = before.shape[:2]
        x1, y1, x2, y2 = damage_bbox
        rx1, ry1 = int(x1 * w), int(y1 * h)
        rx2, ry2 = int(x2 * w), int(y2 * h)
        b = before[ry1:ry2, rx1:rx2]
        a = after[ry1:ry2, rx1:rx2]
    else:
        b, a = before, after

    eb = edge_density(b)
    ea = edge_density(a)
    db = damage_score(b)
    da = damage_score(a)

    edge_red = (eb - ea) / eb if eb > 0 else 0.0
    dmg_red = (db - da) / db if db > 0 else 0.0

    return {
        "edge_before": round(eb, 4),
        "edge_after": round(ea, 4),
        "edge_reduction_pct": round(edge_red * 100, 2),
        "damage_before": round(db, 4),
        "damage_after": round(da, 4),
        "damage_reduction_pct": round(dmg_red * 100, 2),
    }


def colour_drift(before: np.ndarray, after: np.ndarray) -> dict:
    """
    Mean HSV shift between images.
    Large shifts suggest different scene rather than repair.
    """
    hsv_b = cv2.cvtColor(before, cv2.COLOR_BGR2HSV).astype(float)
    hsv_a = cv2.cvtColor(after, cv2.COLOR_BGR2HSV).astype(float)
    delta = np.abs(hsv_b - hsv_a).mean(axis=(0, 1))
    return {
        "hue_shift": round(float(delta[0]), 2),
        "sat_shift": round(float(delta[1]), 2),
        "val_shift": round(float(delta[2]), 2),
    }
