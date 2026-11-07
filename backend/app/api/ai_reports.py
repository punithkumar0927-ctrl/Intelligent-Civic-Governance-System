"""Evidence-grounded issue narratives. The LLM is not asked to invent findings."""

import sys
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.database import get_db
from app.models.issue import Issue

router = APIRouter(prefix="/api/ai-reports", tags=["AI Reports"])


def _generator():
    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ai_engine.generative_ai.llm_provider import complete
    from ai_engine.generative_ai.report_generator import build_report_text
    return complete, build_report_text


@router.get("/{issue_id}")
def issue_report(
    issue_id: int,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if user.role == "citizen" and issue.reporter_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed to view this report")

    location = ", ".join(part for part in [issue.address_raw, issue.ward, issue.city] if part) or "coordinates submitted with the report"
    if issue.latitude is None or issue.longitude is None:
        location = location if issue.address_raw or issue.ward or issue.city else "location was not provided"

    detection = issue.ai_detected_label or "no road-damage class was returned"
    if issue.ai_status == "MODEL_NOT_CONFIGURED":
        detection = "the road-damage model is not configured, so no class was detected"

    complete, build_report_text = _generator()
    fallback = build_report_text(
        title=issue.title,
        category=issue.category.value if issue.category else "other",
        severity=issue.severity.value if issue.severity else "low",
        location_str=location,
        ward=issue.ward,
        city=issue.city,
        description=issue.description or "",
        days_open=0,
        duplicate_count=1 if issue.is_duplicate else 0,
        image_count=len(issue.evidence or []),
        status=issue.status.value if issue.status else "pending",
    )
    grounded = (
        f"{fallback}\n\nDetection status: {issue.ai_status or 'not run'}. "
        f"Stored finding: {detection}. "
        "This text uses saved report fields only. It does not confirm a repair, a government action, "
        "or an official engineering assessment."
    )
    generated = complete(grounded, grounded)
    return {
        "issue_id": issue.id,
        "source": generated["source"],
        "note": generated["note"],
        "report": generated["text"],
        "limitations": "Human review is required before any operational decision.",
    }
