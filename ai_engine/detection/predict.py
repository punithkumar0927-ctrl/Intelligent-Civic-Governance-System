"""
ai_engine/detection/predict.py
Standalone inference runner for NEXUS AI vision pipeline.
Use for testing or batch-processing without the full FastAPI server.

Usage:
    python predict.py --image ./test_pothole.jpg --model ../backend/models/yolov8n_infrastructure.pt
    python predict.py --batch ./test_images/ --output ./results.json
"""

import argparse
import json
import sys
from pathlib import Path

# Add backend to path so we can reuse vision_service
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.services.vision_service import detect_issue, compute_image_features, compare_images


def detect_image(image_path: str, model=None) -> dict:
    """Run road-damage detection, or report that weights are not configured."""
    from ai_engine.detection.model_loader import NOT_CONFIGURED, load_yolo

    if model is None:
        model, _path = load_yolo()
    if model is None:
        return {"status": "MODEL_NOT_CONFIGURED", "detections": [], "message": NOT_CONFIGURED}
    try:
        results = model.predict(image_path, conf=0.25, verbose=False)
    except Exception as exc:
        return {"status": "error", "detections": [], "message": str(exc)}
    detections = []
    for result in results:
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            continue
        for box in boxes:
            cls_id = int(box.cls[0])
            label = model.names.get(cls_id, str(cls_id)) if isinstance(model.names, dict) else str(cls_id)
            xyxy = box.xyxy[0].tolist()
            detections.append({
                "class": label,
                "confidence": float(box.conf[0]),
                "bounding_box": {"x1": xyxy[0], "y1": xyxy[1], "x2": xyxy[2], "y2": xyxy[3]},
            })
    return {"status": "completed", "detections": detections}


def predict_single(image_path: str, save_annotated: bool = False) -> dict:
    result = detect_issue(image_path)
    features = compute_image_features(image_path)
    output = {
        "image": image_path,
        "detection": result,
        "features": features,
    }
    if save_annotated and result and (result.get("max_confidence") or 0) > 0.30:
        print("Annotated export requires the configured road-damage weights. No COCO model is loaded.")
    return output


def predict_batch(folder: str, output_json: str) -> None:
    exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    results = []
    for p in Path(folder).glob("*"):
        if p.suffix.lower() in exts:
            print(f"Processing: {p}")
            results.append(predict_single(str(p)))
    Path(output_json).write_text(json.dumps(results, indent=2, default=str))
    print(f"\nSaved {len(results)} results → {output_json}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image",  help="Single image path")
    parser.add_argument("--batch",  help="Folder of images")
    parser.add_argument("--output", default="./detection_results.json")
    parser.add_argument("--annotate", action="store_true")
    args = parser.parse_args()

    if args.batch:
        predict_batch(args.batch, args.output)
    elif args.image:
        r = predict_single(args.image, args.annotate)
        print(json.dumps(r, indent=2, default=str))
    else:
        parser.print_help()
