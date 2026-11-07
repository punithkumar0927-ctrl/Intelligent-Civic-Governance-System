"""
ai_engine/resolution_verification/compare_images.py
Top-level before/after comparison orchestrator.
Returns a structured result used by the backend verification service.
"""
import numpy as np
from pathlib import Path
from typing import Union

from ai_engine.resolution_verification.image_alignment import align_pair
from ai_engine.resolution_verification.damage_comparison import (
    ssim_single,
    edge_density,
    region_comparison,
    colour_drift,
    pixel_diff,
)


def compare_images(
    before_path: Union[str, Path],
    after_path: Union[str, Path],
    damage_bbox: tuple | None = None,   # (x1,y1,x2,y2) normalised; None = full image
    target_size: tuple = (640, 480),
) -> dict:
    """
    Full before/after comparison pipeline.

    Returns:
    {
      "ssim_score":         float,    # structural similarity (higher = more similar scene)
      "edge_before":        float,    # edge density in before
      "edge_after":         float,    # edge density in after
      "edge_reduction_pct": float,    # % reduction in edge density (repair signal)
      "brightness_delta":   int,      # mean grayscale shift
      "colour_drift":       dict,     # HSV shifts
      "pixel_diff":         dict,     # raw pixel statistics
      "resolved_probability": float,  # 0-1 AI confidence
      "recommendation":     str,      # human-readable label
    }
    """
    before_img, after_img = align_pair(before_path, after_path, target_size)

    ssim = ssim_single(before_img, after_img)
    reg  = region_comparison(before_img, after_img, damage_bbox)

    eb = edge_density(before_img)
    ea = edge_density(after_img)

    grey_b = int(np.mean(
        cv2.cvtColor(before_img, cv2.COLOR_BGR2GRAY)
        if len(before_img.shape) == 3 else before_img
    )) if True else 0
    grey_a = int(np.mean(
        cv2.cvtColor(after_img, cv2.COLOR_BGR2GRAY)
        if len(after_img.shape) == 3 else after_img
    )) if True else 0
    brightness_delta = grey_a - grey_b

    drift = colour_drift(before_img, after_img)
    pdiff = pixel_diff(before_img, after_img)

    # Compute resolved probability
    prob = _resolved_probability(ssim, reg, drift)
    rec  = _label(prob, reg["edge_reduction_pct"])

    return {
        "ssim_score": ssim,
        "edge_before": eb,
        "edge_after": ea,
        "edge_reduction_pct": reg["edge_reduction_pct"],
        "brightness_delta": brightness_delta,
        "colour_drift": drift,
        "pixel_diff": pdiff,
        "resolved_probability": prob,
        "recommendation": rec,
    }


import cv2  # noqa: E402 (needed for the brightness calc above)


def _resolved_probability(ssim: float, reg: dict, drift: dict) -> float:
    """
    Combine signals into resolved_probability.
    - High edge reduction + moderate SSIM = repair visible
    - Large colour drift = different scene (penalty)
    - Very high SSIM = nothing changed (penalty)
    """
    edge_red = max(0.0, reg["edge_reduction_pct"]) / 100.0  # 0-1
    dmg_red  = max(0.0, reg["damage_reduction_pct"]) / 100.0

    # Base: how much damage signal was removed
    base = 0.5 * edge_red + 0.5 * dmg_red

    # SSIM sanity: if images nearly identical SSIM > 0.90 → no change
    if ssim > 0.90:
        base *= 0.2   # penalise strongly

    # Colour drift penalty: large hue shift suggests different angle/scene
    hue_drift = drift["hue_shift"]
    if hue_drift > 30:
        base *= 0.4
    elif hue_drift > 15:
        base *= 0.7

    # Very low edge reduction = likely not fixed
    if edge_red < 0.05:
        base *= 0.3

    return round(min(base + 0.15, 1.0), 4)  # +0.15 floor because some change is visible


def _label(prob: float, edge_red_pct: float) -> str:
    if prob >= 0.75:
        return f"Likely FIXED – damage edges reduced {edge_red_pct:.0f}%"
    if prob >= 0.55:
        return f"PARTIALLY FIXED – damage reduced {edge_red_pct:.0f}%, patch incomplete"
    if prob >= 0.35:
        return "NEEDS HUMAN REVIEW – mixed signals"
    return "NOT FIXED – little or no visible improvement"
