import os
import json
import uuid
from pathlib import Path
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc

from app.database import get_db
from app.models.user import User
from app.models.issue import Issue, IssueCategory, IssueStatus, SeverityLevel
from app.models.evidence import Evidence, EvidenceType
from app.models.resolution import Resolution, VerificationStatus
from app.schemas.schemas import (
    IssueCreate, IssueUpdate, IssueOut, IssueListOut,
    EvidenceOut, AIAnalysisResult
)
from app.core.security import CurrentUser
from app.core.config import settings
from app.services.report_service import analyze_and_save
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/reports", tags=["Reports"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm"}
MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


# ── Helpers ──────────────────────────────────────────────────────────────────
def _save_upload(file: UploadFile, prefix: str) -> tuple[str, str, int]:
    ext = Path(file.filename or "img.jpg").suffix.lower()
    fname = f"{prefix}_{uuid.uuid4().hex}{ext}"
    fpath = UPLOAD_DIR / fname
    content = file.file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413,
                            detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit")
    fpath.write_bytes(content)
    return fname, str(fpath), len(content)


# ── Create Issue (multipart with optional images) ────────────────────────────
@router.post("", response_model=IssueOut, status_code=status.HTTP_201_CREATED)
async def create_report(
    title:       Annotated[str,          Form()],
    description: Annotated[Optional[str], Form()] = None,
    category:    Annotated[IssueCategory, Form()] = IssueCategory.OTHER,
    latitude:    Annotated[Optional[float], Form()] = None,
    longitude:   Annotated[Optional[float], Form()] = None,
    ward:        Annotated[Optional[str],  Form()] = None,
    city:        Annotated[Optional[str],  Form()] = None,
    state:       Annotated[Optional[str],  Form()] = None,
    address_raw: Annotated[Optional[str],  Form()] = None,
    image_before: Annotated[Optional[UploadFile], File()] = None,
    image_after:  Annotated[Optional[UploadFile], File()] = None,
    db:           Annotated[Session, Depends(get_db)] = None,
    user:         CurrentUser = None,
):
    if len(title.strip()) < 5:
        raise HTTPException(status_code=422, detail="Title must be at least 5 characters")
    issue = Issue(
        title=title,
        description=description,
        category=category,
        latitude=latitude,
        longitude=longitude,
        ward=ward,
        city=city,
        state=state,
        address_raw=address_raw,
        reporter_id=user.id,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)

    # Save evidence images
    for file, etype in [(image_before, EvidenceType.IMAGE_BEFORE),
                         (image_after,  EvidenceType.IMAGE_AFTER)]:
        if file and file.content_type in ALLOWED_IMAGE_TYPES:
            fname, fpath, fsize = _save_upload(file, f"issue{issue.id}")
            ev = Evidence(
                issue_id=issue.id,
                uploader_id=user.id,
                evidence_type=etype,
                file_name=file.filename or fname,
                file_path=fpath,
                file_size_bytes=fsize,
                mime_type=file.content_type,
            )
            db.add(ev)
            db.commit()

    # Run AI pipeline (sync in dev; production: background task / queue)
    try:
        await analyze_and_save(db, issue)
    except Exception as exc:
        print(f"[AI pipeline warn] {exc}")   # don't fail report creation on AI error

    db.refresh(issue)
    return IssueOut.model_validate(issue)


# ── List Issues ───────────────────────────────────────────────────────────────
@router.get("", response_model=IssueListOut)
def list_issues(
    db:       Annotated[Session, Depends(get_db)],
    page:     Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    status:   Optional[IssueStatus]   = None,
    category: Optional[IssueCategory] = None,
    severity: Optional[SeverityLevel] = None,
    city:     Optional[str] = None,
    q:        Optional[str] = None,
    mine:     bool = False,
    user:     CurrentUser = None,
):
    query = db.query(Issue)
    if mine:
        query = query.filter(Issue.reporter_id == user.id)
    if status:   query = query.filter(Issue.status   == status)
    if category: query = query.filter(Issue.category == category)
    if severity: query = query.filter(Issue.severity == severity)
    if city:     query = query.filter(Issue.city.ilike(f"%{city}%"))
    if q:        query = query.filter(
                     Issue.title.ilike(f"%{q}%") | Issue.description.ilike(f"%{q}%")
                 )

    total    = query.count()
    items    = (
        query.order_by(Issue.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return IssueListOut(
        items=[IssueOut.model_validate(i) for i in items],
        total=total, page=page, per_page=per_page,
    )


class DeleteReportsIn(BaseModel):
    ids: list[int] = Field(default_factory=list, max_length=100)
    delete_all: bool = False
    confirm: str = ""


def _owned_or_reject(db: Session, user: User, ids: list[int]) -> list[Issue]:
    unique_ids = list(dict.fromkeys(ids))
    if not unique_ids:
        return []
    rows = db.query(Issue).filter(Issue.id.in_(unique_ids)).all()
    found = {row.id: row for row in rows}
    missing = [item for item in unique_ids if item not in found]
    if missing:
        raise HTTPException(status_code=404, detail="Report not found")
    if any(row.reporter_id != user.id for row in rows):
        raise HTTPException(status_code=403, detail="You can only delete your own reports.")
    return [found[item] for item in unique_ids]


def _remove_upload(path_str: str) -> None:
    if not path_str:
        return
    raw = Path(path_str)
    options = [raw]
    if not raw.is_absolute():
        options.append(UPLOAD_DIR / raw.name)
    root = UPLOAD_DIR.resolve()
    for option in options:
        candidate = option.resolve()
        if candidate != root and root not in candidate.parents:
            continue
        if candidate.is_file():
            candidate.unlink()
            return


def delete_owned_reports(db: Session, user: User, ids: list[int]) -> dict:
    issues = _owned_or_reject(db, user, ids)
    if not issues:
        return {"deleted": 0, "file_errors": []}
    issue_ids = [issue.id for issue in issues]
    evidence = db.query(Evidence).filter(Evidence.issue_id.in_(issue_ids)).all()
    paths = [item.file_path for item in evidence if item.file_path]
    db.query(Issue).filter(Issue.ai_duplicate_of_id.in_(issue_ids)).update(
        {Issue.ai_duplicate_of_id: None}, synchronize_session=False
    )
    db.query(Resolution).filter(Resolution.issue_id.in_(issue_ids)).update(
        {Resolution.before_evidence_id: None, Resolution.after_evidence_id: None},
        synchronize_session=False,
    )
    db.flush()
    for issue in issues:
        db.delete(issue)
    db.commit()
    file_errors: list[str] = []
    for path in paths:
        try:
            _remove_upload(path)
        except OSError as exc:
            file_errors.append(f"{path}: {exc.strerror or exc}")
    return {"deleted": len(issue_ids), "file_errors": file_errors}


@router.post("/delete")
def delete_reports(
    body: DeleteReportsIn,
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
):
    if body.delete_all:
        if body.confirm != "DELETE ALL":
            raise HTTPException(status_code=400, detail="Delete all requires confirmation.")
        ids = [row.id for row in db.query(Issue.id).filter(Issue.reporter_id == user.id).all()]
        return delete_owned_reports(db, user, ids)
    if not body.ids:
        raise HTTPException(status_code=400, detail="Choose at least one report.")
    return delete_owned_reports(db, user, body.ids)


@router.delete("/{issue_id}")
def delete_report(
    issue_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
):
    return delete_owned_reports(db, user, [issue_id])


# ── Get single issue ─────────────────────────────────────────────────────────
@router.get("/{issue_id}", response_model=IssueOut)
def get_issue(issue_id: int, db: Annotated[Session, Depends(get_db)], user: CurrentUser):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    issue.view_count += 1
    db.commit()
    return IssueOut.model_validate(issue)


# ── Update issue (officer/admin only) ───────────────────────────────────────
@router.patch("/{issue_id}", response_model=IssueOut)
def update_issue(
    issue_id: int,
    body: IssueUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
):
    if user.role not in ("officer", "admin"):
        raise HTTPException(status_code=403, detail="Officer access required")
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if body.status == IssueStatus.VERIFIED_RESOLVED:
        verified_resolution = db.query(Resolution).filter(
            Resolution.issue_id == issue.id,
            Resolution.human_verified.is_(True),
            Resolution.verification_status == VerificationStatus.CONFIRMED_FIXED,
        ).first()
        if verified_resolution is None:
            raise HTTPException(
                status_code=409,
                detail="A human-verified resolution is required before closing this issue.",
            )
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(issue, k, v)
    if body.status in (IssueStatus.RESOLVED, IssueStatus.VERIFIED_RESOLVED):
        from datetime import datetime, timezone
        issue.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(issue)
    return IssueOut.model_validate(issue)


# ── Upvote ───────────────────────────────────────────────────────────────────
@router.post("/{issue_id}/upvote", response_model=IssueOut)
def upvote(issue_id: int, db: Annotated[Session, Depends(get_db)], user: CurrentUser):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    issue.upvotes += 1
    db.commit()
    db.refresh(issue)
    return IssueOut.model_validate(issue)


# ── Get evidence list for issue ──────────────────────────────────────────────
@router.get("/{issue_id}/evidence", response_model=list[EvidenceOut])
def get_evidence(issue_id: int, db: Annotated[Session, Depends(get_db)], user: CurrentUser):
    return [
        EvidenceOut.model_validate(e)
        for e in db.query(Evidence).filter(Evidence.issue_id == issue_id).all()
    ]


# ── Trigger AI analysis (manual re-run) ─────────────────────────────────────
@router.post("/{issue_id}/analyze", response_model=AIAnalysisResult)
async def analyze_issue(issue_id: int, db: Annotated[Session, Depends(get_db)], user: CurrentUser):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    result = await analyze_and_save(db, issue)
    return result
