"""Homepage demo video. The file is public only after an admin uploads it."""

import json
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from typing import Annotated, Optional

from app.core.config import settings
from app.core.permissions import require_admin
from app.models.user import User

router = APIRouter(prefix="/api/demo-video", tags=["Demo video"])

DEMO_DIR = Path(settings.UPLOAD_DIR).resolve() / "demo"
DEMO_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST = DEMO_DIR / "manifest.json"
MAX_VIDEO = 200 * 1024 * 1024


def _read_manifest() -> dict:
    if not MANIFEST.is_file():
        return {}
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _public(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    path = DEMO_DIR / name
    if not path.is_file():
        return None
    return f"/uploads/demo/{name}"


@router.get("")
def demo_video():
    data = _read_manifest()
    url = _public(data.get("video"))
    if not url:
        return {"available": False}
    return {
        "available": True,
        "url": url,
        "poster": _public(data.get("poster")),
        "captions": _public(data.get("captions")),
    }


@router.post("")
async def upload_demo(
    user: Annotated[User, require_admin],
    video: Annotated[UploadFile, File()],
    poster: Annotated[Optional[UploadFile], File()] = None,
    captions: Annotated[Optional[UploadFile], File()] = None,
):
    if video.content_type not in {"video/mp4", "application/mp4"}:
        raise HTTPException(status_code=415, detail="Upload an MP4 video.")
    video_name = "nexus-demo.mp4"
    destination = DEMO_DIR / video_name
    size = 0
    with destination.open("wb") as handle:
        while True:
            chunk = await video.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_VIDEO:
                handle.close()
                destination.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Demo video exceeds 200MB.")
            handle.write(chunk)
    if size < 1024:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="The video file is empty or too small to be a recording.")
    manifest = {"video": video_name, "uploaded_by": getattr(user, "id", None)}
    if poster is not None:
        raw = await poster.read()
        if raw[:3] == b"\xff\xd8\xff" or raw.startswith(b"\x89PNG") or (raw.startswith(b"RIFF") and raw[8:12] == b"WEBP"):
            poster_name = "poster.jpg" if raw[:3] == b"\xff\xd8\xff" else "poster.png" if raw.startswith(b"\x89PNG") else "poster.webp"
            (DEMO_DIR / poster_name).write_bytes(raw)
            manifest["poster"] = poster_name
    if captions is not None:
        text = (await captions.read()).decode("utf-8", errors="replace")
        if "WEBVTT" not in text[:40]:
            raise HTTPException(status_code=415, detail="Captions must be a WebVTT file.")
        (DEMO_DIR / "captions.vtt").write_text(text, encoding="utf-8")
        manifest["captions"] = "captions.vtt"
    MANIFEST.write_text(json.dumps(manifest), encoding="utf-8")
    return demo_video()
