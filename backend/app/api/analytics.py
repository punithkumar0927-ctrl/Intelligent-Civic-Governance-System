from typing import Annotated
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.issue import Issue, IssueStatus, SeverityLevel
from app.models.resolution import Resolution, VerificationStatus
from app.schemas.schemas import (
    DashboardStats, CategoryCount, StatusCount,
    SeverityCount, GeoPoint
)
from app.core.security import CurrentUser

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/public")
def public_summary(db: Annotated[Session, Depends(get_db)]):
    """Aggregate counts for the public landing page. No coordinates or personal data."""
    total = db.query(Issue).count()
    by_severity = {
        level.value: db.query(Issue).filter(Issue.severity == level).count()
        for level in SeverityLevel
    }
    return {
        "total_reports": total,
        "by_severity": by_severity,
        "note": "Counts come from stored reports. They are not municipal performance claims.",
    }


@router.get("/dashboard", response_model=DashboardStats)
def dashboard_stats(
    db: Annotated[Session, Depends(get_db)],
    city: Annotated[str | None, Query()] = None,
    user: CurrentUser = None,
):
    base = db.query(Issue)
    if city:
        base = base.filter(Issue.city.ilike(f"%{city}%"))

    total = base.count()
    active = base.filter(Issue.status.in_([
        IssueStatus.PENDING,
        IssueStatus.UNDER_REVIEW,
        IssueStatus.IN_PROGRESS,
    ])).count()
    resolved = base.filter(Issue.status.in_([
        IssueStatus.RESOLVED,
        IssueStatus.VERIFIED_RESOLVED,
    ])).count()
    verified = (
        db.query(func.count(func.distinct(Resolution.issue_id)))
        .join(Issue, Issue.id == Resolution.issue_id)
        .filter(
            Resolution.human_verified.is_(True),
            Resolution.verification_status == VerificationStatus.CONFIRMED_FIXED,
        )
    )
    if city:
        verified = verified.filter(Issue.city.ilike(f"%{city}%"))
    verified_count = verified.scalar() or 0
    pending = base.filter(Issue.status.in_([
        IssueStatus.PENDING,
        IssueStatus.UNDER_REVIEW,
    ])).count()
    critical = base.filter(Issue.severity == SeverityLevel.CRITICAL).count()
    high_severity = base.filter(Issue.severity.in_([
        SeverityLevel.HIGH,
        SeverityLevel.CRITICAL,
    ])).count()
    duplicates = base.filter(Issue.is_duplicate.is_(True)).count()
    demo_count = base.filter(Issue.description.like("SAMPLE DEMO DATA:%")).count()

    # Avg resolution days
    resolved_rows = base.filter(
        Issue.status.in_([IssueStatus.RESOLVED, IssueStatus.VERIFIED_RESOLVED]),
        Issue.resolved_at.isnot(None),
    ).all()
    if resolved_rows:
        deltas = [
            (r.resolved_at - r.created_at).total_seconds() / 86400
            for r in resolved_rows
            if r.resolved_at and r.created_at
        ]
        avg_days = round(sum(deltas) / len(deltas), 2) if deltas else 0.0
    else:
        avg_days = 0.0

    res_rate = round((verified_count / total) * 100, 2) if total else 0.0

    # Category breakdown
    cat_rows = (
        base.with_entities(Issue.category, func.count(Issue.id).label("cnt"))
        .group_by(Issue.category).all()
    )
    by_cat = [CategoryCount(category=c.value if hasattr(c, "value") else str(c), count=n)
              for c, n in cat_rows]

    # Status breakdown
    st_rows = (
        base.with_entities(Issue.status, func.count(Issue.id).label("cnt"))
        .group_by(Issue.status).all()
    )
    by_st = [StatusCount(status=s.value if hasattr(s, "value") else str(s), count=n)
             for s, n in st_rows]

    # Severity breakdown
    sv_rows = (
        base.with_entities(Issue.severity, func.count(Issue.id).label("cnt"))
        .group_by(Issue.severity).all()
    )
    by_sv = [SeverityCount(severity=s.value if hasattr(s, "value") else str(s), count=n)
             for s, n in sv_rows]

    # Geo points for map (max 500)
    geo_rows = (
        base.with_entities(Issue.id, Issue.latitude, Issue.longitude,
                           Issue.severity, Issue.category, Issue.status)
        .filter(Issue.latitude.isnot(None), Issue.longitude.isnot(None))
        .limit(500).all()
    )
    geo_points = [
        GeoPoint(
            id=r[0], lat=float(r[1]), lon=float(r[2]),
            severity=r[3].value if hasattr(r[3], "value") else str(r[3]),
            category=r[4].value if hasattr(r[4], "value") else str(r[4]),
            status=r[5].value if hasattr(r[5], "value") else str(r[5]),
        )
        for r in geo_rows
    ]

    return DashboardStats(
        total_issues=total,
        active_issues=active,
        high_severity_issues=high_severity,
        resolved_issues=resolved,
        verified_resolutions=verified_count,
        duplicate_reports=duplicates,
        ai_detection_accuracy=None,
        demo_data=total > 0 and demo_count == total,
        pending_issues=pending,
        critical_issues=critical,
        avg_resolution_days=avg_days,
        resolution_rate=res_rate,
        by_category=by_cat,
        by_status=by_st,
        by_severity=by_sv,
        geo_points=geo_points,
    )


@router.get("/trends")
def monthly_trends(
    db: Annotated[Session, Depends(get_db)],
    months: Annotated[int, Query(ge=1, le=24)] = 12,
    user: CurrentUser = None,
):
    """Returns last N months: {month, total, resolved}."""
    now = datetime.now(timezone.utc)
    results = []
    for i in range(months - 1, -1, -1):
        month_index = now.year * 12 + now.month - 1 - i
        year, month = divmod(month_index, 12)
        m_start = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        next_month_index = month_index + 1
        end_year, end_month = divmod(next_month_index, 12)
        m_end = datetime(end_year, end_month + 1, 1, tzinfo=timezone.utc)
        total    = db.query(Issue).filter(Issue.created_at >= m_start, Issue.created_at < m_end).count()
        resolved = db.query(Issue).filter(
            Issue.created_at >= m_start, Issue.created_at < m_end,
            Issue.status.in_([IssueStatus.RESOLVED, IssueStatus.VERIFIED_RESOLVED])
        ).count()
        results.append({
            "month":    m_start.strftime("%Y-%m"),
            "total":    total,
            "resolved": resolved,
        })
    return results
