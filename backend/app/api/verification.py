"""
api/verification.py — Before/after repair verification endpoints.
"""
from typing import Annotated, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.issue import Issue, IssueStatus
from app.models.evidence import Evidence, EvidenceType
from app.models.resolution import Resolution, VerificationStatus
from app.schemas.verification_schema import (
    VerificationResult, VerificationUpdate, VerificationSummary, BeforeAfterPair
)
from app.core.security import CurrentUser
from app.core.permissions import require_officer
from app.services.verification_service import run_verification, get_verification_summary
from app.utils.file_handler import save_upload, get_public_url

router = APIRouter(prefix="/api/verification", tags=["Repair Verification"])


@router.post("/issue/{issue_id}", response_model=VerificationResult,
             status_code=status.HTTP_201_CREATED)
async def submit_after_photo(
    issue_id: int,
    after_image: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
):
    """Upload after-repair image and trigger AI comparison."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Save after image
    path = save_upload(after_image, subfolder=f"issue_{issue_id}")
    ev = Evidence(
        issue_id=issue_id,
        uploader_id=user.id,
        evidence_type=EvidenceType.IMAGE_AFTER,
        file_name=after_image.filename or path.name,
        file_path=str(path),
        file_url=get_public_url(str(path)),
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    # Run or update Resolution record
    result = await run_verification(db, issue_id)
    return result


@router.get("/issue/{issue_id}", response_model=list[VerificationResult])
def get_verifications(
    issue_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
):
    """Get all verification records for an issue."""
    rows = db.query(Resolution).filter(Resolution.issue_id == issue_id).all()
    return [_to_result(r) for r in rows]


@router.patch("/{resolution_id}", response_model=VerificationResult)
def review_verification(
    resolution_id: int,
    body: VerificationUpdate,
    db: Annotated[Session, Depends(get_db)],
    officer: Annotated["User", require_officer],
):
    """Officer manually approves or rejects an AI verification."""
    res = db.query(Resolution).filter(Resolution.id == resolution_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Verification not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(res, k, v)
    if body.human_verified:
        from datetime import datetime, timezone
        res.verified_at = datetime.now(timezone.utc)
        # Also update issue status if confirmed
        if body.verification_status == VerificationStatus.CONFIRMED_FIXED:
            res.issue.status = IssueStatus.VERIFIED_RESOLVED
    db.commit()
    db.refresh(res)
    return _to_result(res)


@router.get("/summary", response_model=VerificationSummary)
def verification_summary(
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
):
    return get_verification_summary(db)


@router.get("/pending-review", response_model=list[BeforeAfterPair])
def pending_human_review(
    db: Annotated[Session, Depends(get_db)],
    officer: Annotated["User", require_officer],
    limit: int = Query(20, ge=1, le=100),
):
    """List issues where AI is uncertain and human review is needed."""
    rows = (
        db.query(Resolution, Issue)
        .join(Issue, Issue.id == Resolution.issue_id)
        .filter(Resolution.verification_status == VerificationStatus.NEEDS_REVIEW)
        .order_by(Resolution.created_at.desc())
        .limit(limit).all()
    )
    result = []
    for res, iss in rows:
        before_ev = db.query(Evidence).filter(
            Evidence.issue_id == iss.id,
            Evidence.evidence_type == EvidenceType.IMAGE_BEFORE,
        ).first()
        after_ev = db.query(Evidence).filter(
            Evidence.issue_id == iss.id,
            Evidence.evidence_type == EvidenceType.IMAGE_AFTER,
        ).first()
        result.append(BeforeAfterPair(
            resolution_id=res.id,
            issue_id=iss.id,
            title=iss.title,
            category=iss.category.value,
            severity=iss.severity.value,
            before_image_url=before_ev.file_url if before_ev else None,
            after_image_url=after_ev.file_url if after_ev else None,
            resolved_probability=res.resolved_probability,
            ssim_score=res.ssim_score,
            ai_recommendation=res.officer_note,
            verification_status=res.verification_status.value,
        ))
    return result


def _to_result(r: Resolution) -> VerificationResult:
    """SQLAlchemy Resolution → Pydantic VerificationResult."""
    return VerificationResult(
        resolution_id=r.id, issue_id=r.issue_id,
        ssim_score=r.ssim_score, edge_density_before=None, edge_density_after=None,
        edge_reduction=r.edge_reduction, brightness_delta=r.brightness_delta,
        resolved_probability=r.resolved_probability,
        ai_recommendation=r.officer_note,
        verification_status=r.verification_status,
        human_verified=r.human_verified,
        officer_note=r.officer_note,
        verified_at=r.verified_at, created_at=r.created_at,
    )
