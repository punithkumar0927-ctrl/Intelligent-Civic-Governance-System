"""
ai_engine/detection/evaluate.py
Evaluate trained YOLOv8 model on validation/test set.

Usage:
    python evaluate.py --model ../models/yolov8n_infrastructure.pt --data ../../datasets/infrastructure_yolo/data.yaml
"""

import argparse
import json
import sys
from pathlib import Path


def evaluate(model_path: str, data_yaml: str, split: str = "val"):
    from ultralytics import YOLO

    print(f"Model: {model_path}")
    print(f"Data:  {data_yaml}")
    print(f"Split: {split}\n")

    model = YOLO(model_path)
    metrics = model.val(
        data=data_yaml,
        split=split,
        imgsz=640,
        conf=0.25,
        iou=0.5,
        plots=True,
        save_json=False,
        device="cpu",
    )

    print("\n── Evaluation Results ─────────────────────────────────")
    print(f"  Precision      : {metrics.box.mp:.4f}")
    print(f"  Recall         : {metrics.box.mr:.4f}")
    print(f"  mAP@0.50       : {metrics.box.map50:.4f}")
    print(f"  mAP@0.50:0.95  : {metrics.box.map:.4f}")

    # Per-class results
    if hasattr(metrics.box, "ap_class_index") and metrics.box.ap_class_index is not None:
        print("\n  Per-class mAP@0.50:")
        class_names = model.names
        for i, cls_idx in enumerate(metrics.box.ap_class_index):
            cls_name = class_names[int(cls_idx)] if int(cls_idx) < len(class_names) else f"class_{cls_idx}"
            ap = metrics.box.maps[i] if i < len(metrics.box.maps) else 0.0
            print(f"    {cls_name:25s}: {ap:.4f}")

    # Speed benchmark
    import time
    from PIL import Image
    import numpy as np

    dummy = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    times = []
    for _ in range(20):
        t0 = time.perf_counter()
        model.predict(dummy, verbose=False, device="cpu")
        times.append(time.perf_counter() - t0)
    avg_ms = (sum(times) / len(times)) * 1000
    print(f"\n  Avg Inference (CPU): {avg_ms:.1f}ms / image")
    print(f"  Approx FPS (CPU)   : {1000/avg_ms:.1f}")

    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Path to .pt model weights")
    parser.add_argument("--data",  default="../../datasets/infrastructure_yolo/data.yaml")
    parser.add_argument("--split", default="val", choices=["val", "test"])
    args = parser.parse_args()
    evaluate(args.model, args.data, args.split)
