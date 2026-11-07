"""
ai_engine/resolution_verification/verify_repair.py
High-level repair verification workflow: takes before/after paths, returns
a RepairVerdict object that the backend service can persist.
"""
from dataclasses import dataclass, field
from typing import Optional, Union
from pathlib import Path

from ai_engine.resolution_verification.compare_images import compare_images


@dataclass
class RepairVerdict:
    issue_id: int
    status: str                  # LIKELY_FIXED | PARTIALLY_FIXED | NEEDS_REVIEW | NOT_FIXED
    confidence: float            # 0-1
    ssim_score: float
    edge_reduction_pct: float
    damage_reduction_pct: float
    brightness_delta: int
    summary: str
    ai_details: dict = field(default_factory=dict)
    needs_human_review: bool = True


# Backend thresholds (mirrored here for standalone use)
CONFIRMED_THRESHOLD = 0.75
LIKELY_THRESHOLD    = 0.55
REVIEW_THRESHOLD    = 0.35


def verify_repair(
    issue_id: int,
    before_path: Union[str, Path],
    after_path: Union[str, Path],
    damage_bbox: Optional[tuple] = None,
) -> RepairVerdict:
    """
    Run the full comparison pipeline and return a RepairVerdict.
    """
    result = compare_images(
        before_path=str(before_path),
        after_path=str(after_path),
        damage_bbox=damage_bbox,
    )

    prob = result["resolved_probability"]
    edge_red = result["edge_reduction_pct"]
    dmg_red = result.get("pixel_diff", {}).get("pct_changed", 0.0)

    if prob >= CONFIRMED_THRESHOLD:
        status = "LIKELY_FIXED"
        needs_review = False
    elif prob >= LIKELY_THRESHOLD:
        status = "PARTIALLY_FIXED"
        needs_review = True
    elif prob >= REVIEW_THRESHOLD:
        status = "NEEDS_REVIEW"
        needs_review = True
    else:
        status = "NOT_FIXED"
        needs_review = True

    summary = result["recommendation"]

    return RepairVerdict(
        issue_id=issue_id,
        status=status,
        confidence=prob,
        ssim_score=result["ssim_score"],
        edge_reduction_pct=edge_red,
        damage_reduction_pct=dmg_red,
        brightness_delta=result["brightness_delta"],
        summary=summary,
        ai_details={
            "edge_before": result.get("edge_before", 0.0),
            "edge_after": result.get("edge_after", 0.0),
            "colour_drift": result.get("colour_drift", {}),
            "pixel_diff": result.get("pixel_diff", {}),
        },
        needs_human_review=needs_review,
    )
