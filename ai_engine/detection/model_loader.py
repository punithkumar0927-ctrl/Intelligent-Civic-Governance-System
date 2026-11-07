"""Load road-damage YOLO weights. Never substitutes a COCO checkpoint."""

from pathlib import Path
import os

COCO_FILENAMES = {
    "yolov8n.pt",
    "yolov8s.pt",
    "yolov8m.pt",
    "yolov8l.pt",
    "yolov8x.pt",
    "yolo11n.pt",
    "yolo11s.pt",
}

NOT_CONFIGURED = (
    "MODEL_NOT_CONFIGURED: trained road-damage weights were not found. "
    "Download RDD2022, convert labels with ai_engine/detection/dataset_converter.py, "
    "train with ai_engine/detection/train.py, and set YOLO_MODEL_PATH to the resulting best.pt. "
    "A general COCO checkpoint is not used, because it does not detect road damage."
)


def candidate_weight_paths() -> list[Path]:
    root = Path(__file__).resolve().parents[2]
    raw = os.environ.get("YOLO_MODEL_PATH", "").strip()
    paths: list[Path] = []
    if raw:
        paths.append(Path(raw))
    paths.extend([
        root / "ai_engine" / "models" / "road_damage" / "best.pt",
        root / "backend" / "models" / "yolov8n_infrastructure.pt",
    ])
    return paths


def resolve_weights() -> Path | None:
    """Return a local weights file that is not a stock COCO checkpoint."""
    for path in candidate_weight_paths():
        if not path.is_file():
            continue
        if path.name.lower() in COCO_FILENAMES:
            continue
        if path.stat().st_size < 1000:
            continue
        return path
    return None


def load_yolo():
    """Return (model, path) or (None, None) when weights are absent."""
    path = resolve_weights()
    if path is None:
        return None, None
    from ultralytics import YOLO
    return YOLO(str(path)), path
