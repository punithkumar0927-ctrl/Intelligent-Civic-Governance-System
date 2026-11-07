"""
utils/file_handler.py — Secure file upload and management.
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException

from app.core.config import settings

UPLOAD_DIR    = Path(settings.UPLOAD_DIR)
THUMB_DIR     = UPLOAD_DIR / "thumbnails"
TEMP_DIR      = UPLOAD_DIR / "temporary"
PROCESSED_DIR = UPLOAD_DIR / "processed"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/bmp",
    "image/tiff", "video/mp4", "video/quicktime",
    "audio/mpeg", "audio/mp4", "audio/wav",
    "application/pdf",
}

for d in [UPLOAD_DIR, THUMB_DIR, TEMP_DIR, PROCESSED_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: Optional[str]) -> str:
    """Return a safe UUID-based filename preserving extension."""
    if not filename:
        return "image.jpg"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".jpg"
    return f"{uuid.uuid4().hex}{ext}"


def validate_upload(file: UploadFile) -> None:
    """Raise HTTPException for invalid files before saving."""
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported MIME type: {file.content_type}. "
                   f"Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}"
        )
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    # Check size without loading full file into memory
    file.file.seek(0, 2)  # seek to end
    size = file.file.tell()
    file.file.seek(0)    # reset
    if size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File size {size // (1024*1024)}MB exceeds limit "
                   f"of {settings.MAX_FILE_SIZE_MB}MB"
        )


def save_upload(file: UploadFile, subfolder: str = "") -> Path:
    """
    Validate and save an uploaded file. Returns absolute path.
    Usage: path = save_upload(file, subfolder=f"issue_{issue_id}")
    """
    validate_upload(file)
    folder = UPLOAD_DIR / subfolder if subfolder else UPLOAD_DIR
    folder.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(file.filename)
    dest = folder / safe_name
    with open(dest, "wb") as buf:
        shutil.copyfileobj(file.file, buf)
    return dest


def create_thumbnail(src: Path, max_size: int = 300) -> Optional[Path]:
    """Generate JPEG thumbnail. Returns path to thumbnail or None on failure."""
    try:
        from PIL import Image
        img = Image.open(src)
        img.thumbnail((max_size, max_size), Image.LANCZOS)
        thumb_path = THUMB_DIR / f"thumb_{src.stem}.jpg"
        img.convert("RGB").save(thumb_path, "JPEG", quality=80)
        return thumb_path
    except Exception as exc:
        print(f"[file_handler] thumbnail error: {exc}")
        return None


def delete_file(path: str | Path) -> bool:
    """Safely delete a file. Returns True if deleted."""
    try:
        p = Path(path)
        if p.exists() and p.is_file():
            p.unlink()
            return True
    except Exception as exc:
        print(f"[file_handler] delete error: {exc}")
    return False


def get_file_size(path: str | Path) -> int:
    """Returns file size in bytes (0 if not found)."""
    try:
        return Path(path).stat().st_size
    except Exception:
        return 0


def get_public_url(rel_path: str) -> str:
    """Construct the public URL for an uploaded file."""
    clean = rel_path.lstrip("/").replace("\\", "/")
    return f"/uploads/{clean}"
