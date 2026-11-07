"""Administrator and reviewer endpoints. Permissions are enforced here, not only in the UI."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.permissions import require_admin, require_officer
from app.database import get_db
from app.models.activity import ActivityLog
from app.models.issue import Issue, IssueStatus
from app.models.user import User
from app.schemas.schemas import IssueOut, UserOut

router = APIRouter(prefix="/api/admin", tags=["Administration"])


class StatusUpdate(BaseModel):
    status: IssueStatus
    note: Optional[str] = None


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, require_admin],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
):
    rows = (
        db.query(User)
        .order_by(User.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return [UserOut.model_validate(row) for row in rows]


@router.get("/reports", response_model=list[IssueOut])
def list_reports(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, require_officer],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
):
    rows = (
        db.query(Issue)
        .order_by(Issue.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return [IssueOut.model_validate(row) for row in rows]


@router.patch("/reports/{issue_id}/status", response_model=IssueOut)
def update_status(
    issue_id: int,
    body: StatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, require_officer],
):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    issue.status = body.status
    if body.note:
        issue.resolution_note = body.note
    db.add(ActivityLog(
        actor_id=user.id,
        action="issue_status",
        resource_type="issue",
        resource_id=str(issue.id),
        detail=body.status.value,
    ))
    db.commit()
    db.refresh(issue)
    return IssueOut.model_validate(issue)


@router.get("/audit-logs")
def audit_logs(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, require_admin],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 50,
):
    query = db.query(ActivityLog).order_by(ActivityLog.id.desc())
    total = query.count()
    rows = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "total": total,
        "page": page,
        "items": [
            {
                "id": row.id,
                "actor_id": row.actor_id,
                "action": row.action,
                "resource_type": row.resource_type,
                "resource_id": row.resource_id,
                "detail": row.detail,
                "created_at": row.created_at,
            }
            for row in rows
        ],
    }
