"""Private GPS photographs. There is no Supabase project in this app."""

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import CurrentUser
from app.database import get_db
from app.models.gps_photo import GpsPhoto

router = APIRouter(prefix="/api/gps-photos", tags=["GPS Photos"])

PRIVATE_DIR = Path(settings.UPLOAD_DIR).resolve().parent / "private_storage" / "gps"
PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


class GpsPhotoOut(BaseModel):
    id: int
    original_filename: str
    mime_type: str
    file_size_bytes: int
    latitude: Optional[float]
    longitude: Optional[float]
    gps_accuracy: Optional[float]
    location_address: Optional[str]
    captured_at: datetime
    uploaded_at: Optional[datetime]
    watermark_enabled: bool
    upload_status: str = "uploaded"

    class Config:
        from_attributes = True


def _sniff(data: bytes) -> Optional[str]:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _read_limited(upload: UploadFile) -> bytes:
    content = upload.file.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"Image exceeds {settings.MAX_FILE_SIZE_MB}MB.")
    kind = _sniff(content)
    if not kind:
        raise HTTPException(status_code=415, detail="Upload a JPG, PNG, or WEBP photograph.")
    return content


def _write(content: bytes, suffix: str) -> str:
    name = f"{uuid.uuid4().hex}{suffix}"
    (PRIVATE_DIR / name).write_bytes(content)
    return name


def _suffix(mime: str) -> str:
    return { "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp" }[mime]


@router.get("")
def list_photos(
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
    on: Optional[str] = None,
    location: Optional[str] = None,
    has_location: Optional[bool] = None,
):
    query = db.query(GpsPhoto).filter(GpsPhoto.user_id == user.id)
    if on:
        try:
            day = datetime.strptime(on, "%Y-%m-%d").date()
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Use a YYYY-MM-DD date.") from exc
        start = datetime(day.year, day.month, day.day)
        query = query.filter(GpsPhoto.captured_at >= start, GpsPhoto.captured_at < start + timedelta(days=1))
    if location:
        query = query.filter(GpsPhoto.location_address.ilike(f"%{location}%"))
    if has_location is True:
        query = query.filter(GpsPhoto.latitude.isnot(None), GpsPhoto.longitude.isnot(None))
    if has_location is False:
        query = query.filter(GpsPhoto.latitude.is_(None))
    rows = query.order_by(GpsPhoto.captured_at.desc()).limit(200).all()
    return {"items": [GpsPhotoOut.model_validate(row) for row in rows], "total": len(rows)}


@router.post("", status_code=201)
def upload_photo(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    image: Annotated[UploadFile, File()],
    captured_at: Annotated[str, Form()],
    watermark_enabled: Annotated[bool, Form()] = False,
    latitude: Annotated[Optional[float], Form()] = None,
    longitude: Annotated[Optional[float], Form()] = None,
    gps_accuracy: Annotated[Optional[float], Form()] = None,
    location_address: Annotated[Optional[str], Form()] = None,
    watermark: Annotated[Optional[UploadFile], File()] = None,
):
    try:
        taken = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="captured_at must be an ISO date and time.") from exc
    if (latitude is None) != (longitude is None):
        raise HTTPException(status_code=422, detail="Latitude and longitude must be sent together.")
    if latitude is not None and not (-90 <= latitude <= 90 and longitude is not None and -180 <= longitude <= 180):
        raise HTTPException(status_code=422, detail="Coordinates are out of range.")
    if latitude is None:
        location_address = None
        gps_accuracy = None
    content = _read_limited(image)
    mime = _sniff(content) or "image/jpeg"
    marked = None
    if watermark_enabled:
        if watermark is None:
            raise HTTPException(status_code=400, detail="The watermarked copy was not included.")
        marked = _read_limited(watermark)
    stored = _write(content, _suffix(mime))
    watermark_name = _write(marked, _suffix(_sniff(marked) or "image/jpeg")) if marked else None
    row = GpsPhoto(
        user_id=user.id,
        original_filename=(image.filename or "photo.jpg")[:255],
        stored_name=stored,
        watermark_stored_name=watermark_name,
        mime_type=mime or "image/jpeg",
        file_size_bytes=len(content),
        latitude=latitude,
        longitude=longitude,
        gps_accuracy=gps_accuracy,
        location_address=(location_address or None),
        captured_at=taken,
        watermark_enabled=bool(watermark_name),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return GpsPhotoOut.model_validate(row)


@router.get("/{photo_id}/file")
def download_photo(
    photo_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
    variant: Annotated[str, Query()] = "original",
):
    row = db.query(GpsPhoto).filter(GpsPhoto.id == photo_id, GpsPhoto.user_id == user.id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Photograph not found")
    name = row.watermark_stored_name if variant == "watermark" and row.watermark_stored_name else row.stored_name
    path = PRIVATE_DIR / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="The stored photograph file is missing.")
    return FileResponse(path, media_type=row.mime_type, filename=row.original_filename)


@router.delete("/{photo_id}")
def delete_photo(photo_id: int, db: Annotated[Session, Depends(get_db)], user: CurrentUser):
    row = db.query(GpsPhoto).filter(GpsPhoto.id == photo_id, GpsPhoto.user_id == user.id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Photograph not found")
    names = [row.stored_name, row.watermark_stored_name]
    db.delete(row)
    db.commit()
    errors = []
    for name in names:
        if not name:
            continue
        path = (PRIVATE_DIR / name).resolve()
        if PRIVATE_DIR.resolve() not in path.parents:
            continue
        try:
            if path.is_file():
                path.unlink()
        except OSError as exc:
            errors.append(str(exc))
    return {"deleted": 1, "file_errors": errors}
