"""Road-damage detection API. Missing weights return MODEL_NOT_CONFIGURED."""

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import CurrentUser
from app.database import get_db
from app.models.evidence import Evidence
from app.models.issue import Issue
from app.services.vision_service import detect_issue

router = APIRouter(prefix="/api/detection", tags=["Detection"])


@router.post("/predict")
async def predict(
    user: CurrentUser,
    image: Annotated[UploadFile, File()],
):
    content = await image.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty upload")
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File is too large")
    dest = Path(settings.UPLOAD_DIR) / f"predict_{uuid.uuid4().hex}.jpg"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    result = detect_issue(str(dest))
    return {
        "status": result.get("status") if result else "error",
        "detections": (result or {}).get("detections", []),
        "message": (result or {}).get("message"),
        "requested_by": user.id,
    }


@router.get("/{issue_id}")
def issue_detections(
    issue_id: int,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if user.role == "citizen" and issue.reporter_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed to view this report")
    evidence = db.query(Evidence).filter(Evidence.issue_id == issue.id).all()
    return {
        "issue_id": issue.id,
        "detection_status": issue.ai_status,
        "detected_label": issue.ai_detected_label,
        "confidence": issue.ai_confidence,
        "evidence": [
            {
                "id": item.id,
                "file_name": item.file_name,
                "yolo_label": item.yolo_label,
                "yolo_confidence": item.yolo_confidence,
                "analysis": item.ai_analysis,
            }
            for item in evidence
        ],
    }
