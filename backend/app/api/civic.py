"""Citizen reports, jurisdiction lookup, and official review.

Janaspandana iPGRS (https://ipgrs.karnataka.gov.in/), Panchatantra, and Panchamitra
do not have a submission credential in this project. Reports stay in NEXUS AI.
"""

import csv
import io
import json
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import CurrentUser
from app.database import get_db
from app.models.civic import (
    AdministrativeBoundary, AuthorityDirectory, CitizenFeedback, CitizenReport,
    GramPanchayat, IssueCategory, Notification, OfficialActionRecord, ReportAssignment,
    ReportMedia, ReportStatusHistory, RoutingRule, TalukPanchayat, UrbanLocalBody, ZillaPanchayat,
)
from app.models.user import User
from app.services.jurisdiction import ancestor_names, locate
from app.services.vision_service import detect_issue, hamming_distance

router = APIRouter(prefix="/api/civic", tags=["Civic reports"])

CATEGORIES = [
    "Damaged roads and potholes",
    "Garbage accumulation",
    "Drainage and sewage problems",
    "Drinking water problems",
    "Broken streetlights",
    "Public sanitation",
    "Flooding and waterlogging",
    "Damaged public infrastructure",
    "Public building maintenance",
    "Other civic issues",
]
ROAD_LABELS = {"d00", "d10", "d20", "d40", "pothole", "road_damage"}
PRIVATE_DIR = Path(settings.UPLOAD_DIR).resolve().parent / "private_storage" / "civic"
PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024

GOVERNMENT = {
    "janaspandana_ipgrs": {
        "portal": "https://ipgrs.karnataka.gov.in/",
        "api_configured": False,
        "note": "No iPGRS API credential is configured. NEXUS AI does not submit grievances to Janaspandana.",
    },
    "panchatantra": {
        "api_configured": False,
        "note": "No Panchatantra 2.0 submission API is configured.",
    },
    "panchamitra": {
        "api_configured": False,
        "note": "Panchamitra is a government WhatsApp service. NEXUS AI does not send WhatsApp messages or claim a Panchamitra ticket.",
    },
}


def _ensure_categories(db: Session) -> None:
    existing = {row.name for row in db.query(IssueCategory).all()}
    for name in CATEGORIES:
        if name not in existing:
            db.add(IssueCategory(name=name))
    db.commit()


def _sniff(data: bytes) -> Optional[str]:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    if len(data) >= 12 and data[4:8] == b"ftyp":
        return "video/mp4"
    if data.startswith(b"\x1a\x45\xdf\xa3"):
        return "video/webm"
    return None


def _history(db: Session, report: CitizenReport, status: str, actor: Optional[int], source: str, note: str) -> None:
    db.add(ReportStatusHistory(report_id=report.id, status=status, actor_id=actor, source=source, note=note))


def _notify(db: Session, user_id: int, report_id: int, kind: str, message: str) -> None:
    db.add(Notification(user_id=user_id, report_id=report_id, kind=kind, message=message))


def _subtree(db: Session, root_id: int) -> set[int]:
    found = {root_id}
    frontier = [root_id]
    while frontier:
        children = [row[0] for row in db.query(AdministrativeBoundary.id).filter(AdministrativeBoundary.parent_id.in_(frontier)).all()]
        frontier = [item for item in children if item not in found]
        found.update(frontier)
    return found


def _visible(db: Session, user: User, report: CitizenReport) -> bool:
    if user.role == "admin" or report.citizen_id == user.id or report.assigned_official_id == user.id:
        return True
    if user.role in {"gp_official", "taluk_official", "zilla_official"} and user.jurisdiction_boundary_id and report.boundary_id:
        return report.boundary_id in _subtree(db, user.jurisdiction_boundary_id)
    return False


def _serialize(db: Session, report: CitizenReport) -> dict:
    authority = db.query(AuthorityDirectory).filter(AuthorityDirectory.id == report.authority_id).first() if report.authority_id else None
    history = db.query(ReportStatusHistory).filter(ReportStatusHistory.report_id == report.id).order_by(ReportStatusHistory.id).all()
    return {
        "id": report.id,
        "reference": report.reference,
        "description": report.description,
        "category": report.category,
        "citizen_location": {
            "district": report.citizen_district,
            "taluk": report.citizen_taluk,
            "village": report.citizen_village,
            "gram_panchayat": report.citizen_gram_panchayat,
            "label": "Entered by the citizen. Not a verified boundary match.",
        },
        "verified_jurisdiction": {
            "status": report.jurisdiction_status,
            "state": report.verified_state,
            "district": report.verified_district,
            "taluk": report.verified_taluk,
            "village": report.verified_village,
            "gram_panchayat": report.verified_gram_panchayat,
            "urban_local_body": report.verified_ulb,
        },
        "latitude": report.latitude,
        "longitude": report.longitude,
        "gps_accuracy": report.gps_accuracy,
        "ai": {
            "status": report.ai_status,
            "label": report.ai_label,
            "confidence": report.ai_confidence,
            "severity": report.ai_severity,
            "risk_note": report.ai_risk_note,
            "description": report.ai_description,
            "possible_duplicate_of": report.possible_duplicate_of,
            "label_source": "model" if report.ai_status == "completed" else "none",
        },
        "authority": None if not authority else {
            "id": authority.id,
            "name": authority.name,
            "department": authority.department,
            "verified": authority.verified,
        },
        "status": report.status,
        "official_reference": report.official_reference,
        "official_reference_source": "entered by an authorized NEXUS AI user" if report.official_reference else None,
        "government_delivery": report.government_delivery,
        "created_at": report.created_at,
        "history": [{"status": row.status, "source": row.source, "note": row.note, "created_at": row.created_at} for row in history],
    }


class BoundaryIn(BaseModel):
    level: str
    name: str = Field(min_length=2, max_length=200)
    source: str = Field(min_length=3, max_length=200)
    geometry: dict
    parent_id: Optional[int] = None
    lgd_code: Optional[str] = None
    verified: bool = False


class AuthorityIn(BaseModel):
    name: str
    department: str
    boundary_id: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    verified: bool = False
    notes: Optional[str] = None


class RuleIn(BaseModel):
    category: str
    boundary_level: str
    authority_id: int
    escalation_authority_id: Optional[int] = None
    verified: bool = False
    notes: Optional[str] = None


class OfficialIn(BaseModel):
    user_id: int
    role: str
    boundary_id: int


class ActionIn(BaseModel):
    action: str
    status: Optional[str] = None
    note: Optional[str] = None
    official_reference: Optional[str] = None
    assignee_id: Optional[int] = None


@router.get("/government")
def government_channels():
    return {"integrations": GOVERNMENT, "reports_are_sent_automatically": False}


@router.get("/categories")
def categories(db: Annotated[Session, Depends(get_db)], user: CurrentUser):
    _ensure_categories(db)
    return {"items": CATEGORIES}


@router.post("/reports", status_code=201)
def create_report(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    description: Annotated[str, Form()],
    category: Annotated[str, Form()],
    notify_consent: Annotated[bool, Form()] = False,
    latitude: Annotated[Optional[float], Form()] = None,
    longitude: Annotated[Optional[float], Form()] = None,
    gps_accuracy: Annotated[Optional[float], Form()] = None,
    citizen_district: Annotated[Optional[str], Form()] = None,
    citizen_taluk: Annotated[Optional[str], Form()] = None,
    citizen_village: Annotated[Optional[str], Form()] = None,
    citizen_gram_panchayat: Annotated[Optional[str], Form()] = None,
    photo: Annotated[Optional[UploadFile], File()] = None,
    video: Annotated[Optional[UploadFile], File()] = None,
):
    _ensure_categories(db)
    if category not in CATEGORIES:
        raise HTTPException(status_code=422, detail="Choose one of the listed issue categories.")
    if len(description.strip()) < 10:
        raise HTTPException(status_code=422, detail="Describe the issue in at least 10 characters.")
    if (latitude is None) != (longitude is None):
        raise HTTPException(status_code=422, detail="Latitude and longitude must be sent together.")
    if latitude is not None and not (-90 <= latitude <= 90 and longitude is not None and -180 <= longitude <= 180):
        raise HTTPException(status_code=422, detail="Coordinates are out of range.")
    report = CitizenReport(
        reference=f"NEXUS-{datetime.now(timezone.utc):%Y%m%d}-{secrets.token_hex(4).upper()}",
        citizen_id=user.id,
        description=description.strip(),
        category=category,
        latitude=latitude,
        longitude=longitude,
        gps_accuracy=gps_accuracy,
        citizen_district=citizen_district,
        citizen_taluk=citizen_taluk,
        citizen_village=citizen_village,
        citizen_gram_panchayat=citizen_gram_panchayat,
        jurisdiction_status="pending_verification",
        status="Awaiting jurisdiction verification",
        notify_consent=notify_consent,
        ai_status="not_run",
        ai_risk_note="Not assessed from a photograph. Human review is required.",
    )
    if latitude is not None and longitude is not None:
        match = locate(db, longitude, latitude)
        if match:
            report.boundary_id = match.id
            report.jurisdiction_status = "verified"
            for key, value in ancestor_names(db, match).items():
                setattr(report, key, value)
            rule = db.query(RoutingRule).filter(
                RoutingRule.category == category,
                RoutingRule.boundary_level == match.level,
                RoutingRule.verified.is_(True),
            ).first()
            authority = db.query(AuthorityDirectory).filter(AuthorityDirectory.id == rule.authority_id).first() if rule else None
            if authority and authority.verified:
                report.authority_id = authority.id
                report.status = "Awaiting official forwarding"
            else:
                report.status = "Awaiting official forwarding"
        else:
            report.status = "Awaiting jurisdiction verification"
    db.add(report)
    db.commit()
    db.refresh(report)
    _history(db, report, "Submitted to NEXUS AI", user.id, "citizen", "Saved in NEXUS AI. Not delivered to a government portal.")
    _history(db, report, report.status, user.id, "nexus", "Jurisdiction and routing use only verified stored boundaries and rules.")
    _notify(db, user.id, report.id, "submission", f"{report.reference} is saved in NEXUS AI. It has not been sent to Janaspandana, Panchatantra, or Panchamitra.")
    photo_path = _save_media(db, report, photo, "photo")
    _save_media(db, report, video, "video")
    if photo_path:
        _apply_model(db, report, photo_path)
    db.commit()
    db.refresh(report)
    return _serialize(db, report)


def _save_media(db: Session, report: CitizenReport, upload: Optional[UploadFile], kind: str) -> Optional[str]:
    if upload is None:
        return None
    content = upload.file.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB.")
    mime = _sniff(content)
    if kind == "photo" and mime not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Photograph must be JPG, PNG, or WEBP.")
    if kind == "video" and mime not in {"video/mp4", "video/webm"}:
        raise HTTPException(status_code=415, detail="Video must be MP4 or WEBM.")
    suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "video/mp4": ".mp4", "video/webm": ".webm"}[mime]
    name = f"{uuid.uuid4().hex}{suffix}"
    path = PRIVATE_DIR / name
    path.write_bytes(content)
    phash = None
    if kind == "photo":
        try:
            from app.services.vision_service import compute_phash
            phash = compute_phash(str(path))
        except Exception:
            phash = None
    db.add(ReportMedia(report_id=report.id, stored_name=name, original_filename=(upload.filename or name)[:255], mime_type=mime, media_kind=kind, phash=phash))
    return str(path)


def _apply_model(db: Session, report: CitizenReport, path: str) -> None:
    result = detect_issue(path) or {}
    status = result.get("status")
    if status == "MODEL_NOT_CONFIGURED" or not result.get("top_label"):
        report.ai_status = "MODEL_NOT_CONFIGURED" if status == "MODEL_NOT_CONFIGURED" or not result.get("detections") else "no_detection"
        report.ai_confidence = None
        report.ai_severity = None
        report.ai_description = None
        report.ai_risk_note = "The photograph was stored. No issue class was returned, so a person must review it."
        return
    label = str(result.get("top_label"))
    confidence = float(result.get("max_confidence") or 0)
    report.ai_status = "completed"
    report.ai_label = label
    report.ai_confidence = confidence
    report.ai_description = f"The configured model returned {label} at confidence {confidence:.2f}. This is not verification that the issue exists."
    if label.lower() in ROAD_LABELS and confidence >= 0.75:
        report.ai_severity = "High"
    elif confidence >= 0.45:
        report.ai_severity = "Medium"
    else:
        report.ai_severity = "Low"
    report.ai_risk_note = "Model confidence is shown for review. It is not a public-safety determination."
    if confidence < 0.5:
        report.ai_risk_note = "Confidence is below 0.50. Human review is required before this suggestion is used."
    phash = result.get("phash")
    if phash:
        others = db.query(ReportMedia).filter(ReportMedia.phash.isnot(None), ReportMedia.report_id != report.id).all()
        for other in others:
            if hamming_distance(phash, other.phash or "") <= 8:
                report.possible_duplicate_of = other.report_id
                break


@router.get("/reports/mine")
def my_reports(user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    rows = db.query(CitizenReport).filter(CitizenReport.citizen_id == user.id).order_by(CitizenReport.id.desc()).limit(100).all()
    return {"items": [_serialize(db, row) for row in rows]}


@router.get("/reports/{reference}")
def get_report(reference: str, user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    report = db.query(CitizenReport).filter(CitizenReport.reference == reference).first()
    if not report or not _visible(db, user, report):
        raise HTTPException(status_code=404, detail="Report not found")
    return _serialize(db, report)


@router.get("/reports/{reference}/media/{media_id}")
def report_media(reference: str, media_id: int, user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    report = db.query(CitizenReport).filter(CitizenReport.reference == reference).first()
    media = db.query(ReportMedia).filter(ReportMedia.id == media_id, ReportMedia.report_id == (report.id if report else 0)).first()
    if not report or not media or not _visible(db, user, report):
        raise HTTPException(status_code=404, detail="File not found")
    path = PRIVATE_DIR / media.stored_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type=media.mime_type, filename=media.original_filename)


@router.post("/reports/{reference}/feedback")
def feedback(reference: str, satisfied: bool, user: CurrentUser, db: Annotated[Session, Depends(get_db)], comment: Optional[str] = None):
    report = db.query(CitizenReport).filter(CitizenReport.reference == reference, CitizenReport.citizen_id == user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    db.add(CitizenFeedback(report_id=report.id, citizen_id=user.id, satisfied=satisfied, comment=comment))
    if report.status == "Awaiting Citizen Feedback":
        report.status = "Resolved" if satisfied else "Reopened"
        _history(db, report, report.status, user.id, "citizen", comment or "Citizen feedback")
        _notify(db, user.id, report.id, "feedback", f"{report.reference} is now {report.status}.")
    db.commit()
    return _serialize(db, report)


@router.get("/queue")
def official_queue(user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    if user.role not in {"gp_official", "taluk_official", "zilla_official", "admin"}:
        raise HTTPException(status_code=403, detail="An authorized jurisdiction role is required.")
    if user.role != "admin" and not user.jurisdiction_boundary_id:
        return {"items": [], "note": "No verified jurisdiction is assigned to this account."}
    rows = db.query(CitizenReport).order_by(CitizenReport.id.desc()).limit(300).all()
    visible = [row for row in rows if _visible(db, user, row)]
    return {"items": [_serialize(db, row) for row in visible]}


@router.post("/reports/{reference}/actions")
def official_action(reference: str, body: ActionIn, user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    report = db.query(CitizenReport).filter(CitizenReport.reference == reference).first()
    if not report or not _visible(db, user, report) or user.role == "citizen":
        raise HTTPException(status_code=404, detail="Report not found")
    if body.action == "confirm_receipt":
        report.status = "Submitted to authority"
        report.government_delivery = "receipt_confirmed_by_nexus_official"
        note = (body.note or "An authorized NEXUS AI official confirmed receipt.") + " This is not a Janaspandana or Panchamitra acknowledgement."
    elif body.action == "assign":
        assignee = db.query(User).filter(User.id == body.assignee_id).first()
        if not assignee or assignee.jurisdiction_boundary_id != user.jurisdiction_boundary_id:
            raise HTTPException(status_code=422, detail="Assignee must be an official linked to the same verified boundary.")
        report.assigned_official_id = assignee.id
        report.status = "Assigned"
        db.add(ReportAssignment(report_id=report.id, official_id=assignee.id, assigned_by=user.id))
        note = body.note or "Assigned inside NEXUS AI."
        _notify(db, assignee.id, report.id, "assignment", f"{report.reference} was assigned to your NEXUS AI account.")
    elif body.action == "status":
        allowed = {"Acknowledged", "In Progress", "Action Taken", "Awaiting Citizen Feedback", "Resolved", "Escalated"}
        if body.status not in allowed:
            raise HTTPException(status_code=422, detail="Choose a status from the official action list. Submitted to authority requires confirm_receipt.")
        report.status = body.status
        note = body.note or body.status
    elif body.action == "reject":
        if not body.note:
            raise HTTPException(status_code=422, detail="A rejection reason is required.")
        report.status = "Rejected with Reason"
        note = body.note
    elif body.action == "request_info":
        report.status = "Awaiting Citizen Feedback"
        note = body.note or "More information was requested."
    elif body.action == "record_official_reference":
        if not body.official_reference:
            raise HTTPException(status_code=422, detail="Enter the reference from the government channel.")
        report.official_reference = body.official_reference[:80]
        note = "Government reference recorded by a NEXUS AI user. It was not fetched from a portal."
    else:
        raise HTTPException(status_code=422, detail="Unknown action.")
    db.add(OfficialActionRecord(report_id=report.id, official_id=user.id, action=body.action, note=note))
    _history(db, report, report.status, user.id, "nexus_official", note)
    if report.notify_consent:
        _notify(db, report.citizen_id, report.id, "status", f"{report.reference}: {report.status}. {note}")
    db.commit()
    return _serialize(db, report)


@router.get("/notifications")
def notifications(user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    rows = db.query(Notification).filter(Notification.user_id == user.id).order_by(Notification.id.desc()).limit(50).all()
    return {"items": [{"id": row.id, "kind": row.kind, "message": row.message, "created_at": row.created_at} for row in rows]}


@router.post("/boundaries", status_code=201)
def add_boundary(body: BoundaryIn, user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access is required.")
    if body.level not in LEVELS:
        raise HTTPException(status_code=422, detail="Level must be state, district, taluk, village, gram_panchayat, or ulb.")
    if body.geometry.get("type") not in {"Polygon", "MultiPolygon"}:
        raise HTTPException(status_code=422, detail="Geometry must be a GeoJSON Polygon or MultiPolygon.")
    row = AdministrativeBoundary(
        level=body.level, name=body.name.strip(), source=body.source.strip(),
        parent_id=body.parent_id, lgd_code=body.lgd_code, verified=body.verified,
        geometry_json=json.dumps(body.geometry),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    _link_body(db, row)
    return {"id": row.id, "name": row.name, "level": row.level, "verified": row.verified, "source": row.source}


LEVELS = {"state", "district", "taluk", "village", "gram_panchayat", "ulb"}


def _link_body(db: Session, row: AdministrativeBoundary) -> None:
    table = {"gram_panchayat": GramPanchayat, "taluk": TalukPanchayat, "district": ZillaPanchayat, "ulb": UrbanLocalBody}.get(row.level)
    if not table:
        return
    if db.query(table).filter(table.boundary_id == row.id).first():
        return
    db.add(table(boundary_id=row.id, name=row.name))
    db.commit()


@router.post("/authorities", status_code=201)
def add_authority(body: AuthorityIn, user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access is required.")
    row = AuthorityDirectory(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "name": row.name, "verified": row.verified}


@router.post("/routing-rules", status_code=201)
def add_rule(body: RuleIn, user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access is required.")
    if body.category not in CATEGORIES:
        raise HTTPException(status_code=422, detail="Unknown category.")
    if not db.query(AuthorityDirectory).filter(AuthorityDirectory.id == body.authority_id).first():
        raise HTTPException(status_code=404, detail="Authority not found")
    row = RoutingRule(**body.model_dump())
    db.add(row)
    db.commit()
    return {"id": row.id, "verified": row.verified}


@router.post("/officials")
def assign_official(body: OfficialIn, user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access is required.")
    if body.role not in {"gp_official", "taluk_official", "zilla_official"}:
        raise HTTPException(status_code=422, detail="Role must be gp_official, taluk_official, or zilla_official.")
    boundary = db.query(AdministrativeBoundary).filter(AdministrativeBoundary.id == body.boundary_id, AdministrativeBoundary.verified.is_(True)).first()
    if not boundary:
        raise HTTPException(status_code=422, detail="Choose a verified stored boundary. A name cannot be assigned without one.")
    account = db.query(User).filter(User.id == body.user_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="User not found")
    account.role = body.role
    account.jurisdiction_boundary_id = boundary.id
    db.commit()
    return {"user_id": account.id, "role": account.role, "boundary_id": boundary.id, "boundary_name": boundary.name}


@router.get("/export")
def export_reports(user: CurrentUser, db: Annotated[Session, Depends(get_db)], file_format: str = "csv"):
    if user.role not in {"zilla_official", "admin"}:
        raise HTTPException(status_code=403, detail="District or administrator access is required.")
    rows = [row for row in db.query(CitizenReport).all() if _visible(db, user, row)]
    header = ["reference", "category", "status", "jurisdiction_status", "verified_district", "verified_taluk", "verified_gram_panchayat", "latitude", "longitude", "official_reference"]
    if file_format == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(header)
        for row in rows:
            writer.writerow([row.reference, row.category, row.status, row.jurisdiction_status, row.verified_district or "", row.verified_taluk or "", row.verified_gram_panchayat or "", row.latitude if row.latitude is not None else "", row.longitude if row.longitude is not None else "", row.official_reference or ""])
        return Response(buffer.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=nexus-district-reports.csv"})
    lines = ["NEXUS AI district report", "Government portal delivery is not connected.", ""]
    for row in rows:
        lines.append(f"{row.reference} | {row.category} | {row.status} | {row.jurisdiction_status}")
    return Response(_pdf(lines), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=nexus-district-reports.pdf"})


def _pdf(lines: list[str]) -> bytes:
    text = "\n".join(lines)[:4000].replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 11 Tf 40 800 Td ({text.replace(chr(10), ') Tj T* (')}) Tj ET"
    objects = [
        "1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj",
        "2 0 obj<< /Type /Pages /Count 1 /Kids [3 0 R] >>endobj",
        "3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj",
        f"4 0 obj<< /Length {len(stream)} >>stream\n{stream}\nendstream endobj",
        "5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj",
    ]
    content = "%PDF-1.4\n" + "\n".join(objects) + "\ntrailer<< /Root 1 0 R >>\n%%EOF"
    return content.encode("latin-1", errors="replace")
