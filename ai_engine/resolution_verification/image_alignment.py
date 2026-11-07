"""
ai_engine/resolution_verification/image_alignment.py
Aligns a before and after image so that comparison operates on matched pixels.
Uses ORB feature matching + homography when available; falls back to resize.
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Optional


def load_image(path: str | Path, max_side: int = 800) -> np.ndarray:
    """Load image as BGR numpy array; downscale for speed."""
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    h, w = img.shape[:2]
    scale = min(max_side / max(h, w), 1.0)
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


def align_pair(
    before_path: str | Path,
    after_path: str | Path,
    target_size: tuple = (640, 480),
) -> tuple[np.ndarray, np.ndarray]:
    """
    Aligns before/after images using ORB feature-based homography.
    Falls back to direct resize if alignment fails (< 4 matches).
    Returns two BGR arrays of identical target_size.
    """
    before = load_image(before_path)
    after  = load_image(after_path)

    tw, th = target_size

    # Try feature-based alignment
    aligned_after: Optional[np.ndarray] = _try_homography(before, after, tw, th)

    if aligned_after is not None:
        before_r = cv2.resize(before, (tw, th))
        return before_r, aligned_after

    # Fallback: simple resize
    return cv2.resize(before, (tw, th)), cv2.resize(after, (tw, th))


def _try_homography(
    before: np.ndarray,
    after: np.ndarray,
    tw: int,
    th: int,
) -> Optional[np.ndarray]:
    """
    ORB keypoints + BFMatcher + findHomography.
    Returns warped after image or None if not enough inliers.
    """
    try:
        gray_b = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
        gray_a = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)

        orb = cv2.ORB_create(nfeatures=500)
        kp_b, des_b = orb.detectAndCompute(gray_b, None)
        kp_a, des_a = orb.detectAndCompute(gray_a, None)

        if des_b is None or des_a is None:
            return None

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        raw = bf.knnMatch(des_b, des_a, k=2)

        # Lowe ratio test
        good = []
        for pair in raw:
            if len(pair) == 2:
                m, n = pair
                if m.distance < 0.75 * n.distance:
                    good.append(m)

        if len(good) < 8:
            return None

        src_pts = np.float32([kp_b[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp_a[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

        H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)
        if H is None or mask is None:
            return None

        inlier_ratio = mask.sum() / len(mask)
        if inlier_ratio < 0.3:
            return None

        warped = cv2.warpPerspective(after, H, (before.shape[1], before.shape[0]))
        return cv2.resize(warped, (tw, th))

    except Exception:
        return None


def crop_damage_region(
    img: np.ndarray,
    bbox: tuple,  # (x1, y1, x2, y2) normalised 0-1
    pad: float = 0.1,
) -> np.ndarray:
    """Crop the damage region with padding; returns sub-image."""
    h, w = img.shape[:2]
    x1, y1, x2, y2 = bbox
    px1 = max(0, int((x1 - pad) * w))
    py1 = max(0, int((y1 - pad) * h))
    px2 = min(w, int((x2 + pad) * w))
    py2 = min(h, int((y2 + pad) * h))
    return img[py1:py2, px1:px2].copy()
