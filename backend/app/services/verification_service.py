"""
services/verification_service.py — Orchestrates before/after repair verification.
"""
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.issue import Issue, IssueStatus
from app.models.evidence import Evidence, EvidenceType
from app.models.resolution import Resolution, VerificationStatus
from app.schemas.verification_schema import VerificationResult, VerificationSummary
from app.services.vision_service import compare_images


# Thresholds for AI verification confidence
CONFIRMED_FIXED_THRESHOLD   = 0.75
LIKELY_FIXED_THRESHOLD      = 0.55
NEEDS_REVIEW_THRESHOLD_LOW  = 0.35  # below this: likely NOT fixed


async def run_verification(db: Session, issue_id: int) -> VerificationResult:
    """
    Find before+after evidence, run AI comparison, create/update Resolution.
    Returns VerificationResult.
    """
    before_ev = db.query(Evidence).filter(
        Evidence.issue_id == issue_id,
        Evidence.evidence_type == EvidenceType.IMAGE_BEFORE,
    ).order_by(Evidence.created_at.asc()).first()

    after_ev = db.query(Evidence).filter(
        Evidence.issue_id == issue_id,
        Evidence.evidence_type == EvidenceType.IMAGE_AFTER,
    ).order_by(Evidence.created_at.desc()).first()

    if not before_ev or not after_ev:
        # Create pending resolution record
        res = _get_or_create_resolution(db, issue_id)
        res.verification_status = VerificationStatus.PENDING
        db.commit(); db.refresh(res)
        return _to_result(res, before_ev, after_ev)

    # Run AI comparison
    try:
        comp = compare_images(before_ev.file_path, after_ev.file_path)
    except Exception as exc:
        print(f"[verification_service] compare error: {exc}")
        comp = {"ssim_score": 0.5, "edge_reduction": 0.0,
                "brightness_delta": 0, "resolved_probability": 0.3,
                "recommendation": "Comparison failed — manual review needed"}

    prob = comp.get("resolved_probability", 0.0)

    # Determine status from probability
    if prob >= CONFIRMED_FIXED_THRESHOLD:
        status = VerificationStatus.LIKELY_FIXED
    elif prob >= LIKELY_FIXED_THRESHOLD:
        status = VerificationStatus.PARTIALLY_FIXED
    elif prob >= NEEDS_REVIEW_THRESHOLD_LOW:
        status = VerificationStatus.NEEDS_REVIEW   # human review required
    else:
        status = VerificationStatus.NOT_FIXED

    res = _get_or_create_resolution(db, issue_id)
    res.before_evidence_id  = before_ev.id
    res.after_evidence_id   = after_ev.id
    res.ssim_score          = comp.get("ssim_score")
    res.edge_reduction      = comp.get("edge_reduction")
    res.brightness_delta    = comp.get("brightness_delta")
    res.resolved_probability = prob
    res.verification_status = status
    res.officer_note        = comp.get("recommendation", "")
    db.commit(); db.refresh(res)

    return _to_result(res, before_ev, after_ev)


def _get_or_create_resolution(db: Session, issue_id: int) -> Resolution:
    res = db.query(Resolution).filter(Resolution.issue_id == issue_id).first()
    if not res:
        res = Resolution(issue_id=issue_id, verification_status=VerificationStatus.PENDING)
        db.add(res)
        db.commit()
        db.refresh(res)
    return res


def _to_result(
    res: Resolution,
    before_ev: Optional[Evidence],
    after_ev:  Optional[Evidence],
) -> VerificationResult:
    return VerificationResult(
        resolution_id=res.id,
        issue_id=res.issue_id,
        ssim_score=res.ssim_score,
        edge_density_before=None,
        edge_density_after=None,
        edge_reduction=res.edge_reduction,
        brightness_delta=res.brightness_delta,
        resolved_probability=res.resolved_probability,
        ai_recommendation=res.officer_note,
        verification_status=res.verification_status,
        human_verified=res.human_verified,
        officer_note=res.officer_note,
        verified_at=res.verified_at,
        created_at=res.created_at,
    )


def get_verification_summary(db: Session) -> VerificationSummary:
    total     = db.query(Resolution).count()
    pending   = db.query(Resolution).filter(
        Resolution.verification_status.in_([
            VerificationStatus.PENDING,
            VerificationStatus.NEEDS_REVIEW,
        ])
    ).count()
    verified  = db.query(Resolution).filter(
        Resolution.verification_status.in_([
            VerificationStatus.CONFIRMED_FIXED,
            VerificationStatus.LIKELY_FIXED,
        ])
    ).count()
    rejected  = db.query(Resolution).filter(
        Resolution.verification_status.in_([
            VerificationStatus.NOT_FIXED,
            VerificationStatus.REJECTED,
        ])
    ).count()

    # Avg confidence of completed verifications
    rows = db.query(Resolution.resolved_probability).filter(
        Resolution.resolved_probability.isnot(None)
    ).all()
    avg_conf = round(
        sum(r[0] for r in rows) / len(rows), 3
    ) if rows else 0.0

    return VerificationSummary(
        total_pending=pending,
        total_verified=verified,
        total_rejected=rejected,
        avg_confidence=avg_conf,
        verification_rate=round((verified / total) * 100, 1) if total else 0.0,
    )
