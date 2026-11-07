"""
ai_engine/detection/train.py
YOLOv8 Fine-Tuning Script for Urban Infrastructure Defect Detection.

Dataset: RDD2022 (Road Damage Detection) — https://github.com/abderyu/RDD2022
      + Roboflow pothole datasets (open-source, CC-BY-4.0)
      + Custom-annotated Indian road scenes

Classes: pothole, crack, garbage, damaged_sidewalk, broken_streetlight,
         water_leak, blocked_drain, damaged_road, overgrown, broken_sign

Usage:
    python train.py --data ./datasets/infrastructure_yolo/data.yaml --epochs 100 --imgsz 640

Output:
    runs/detect/train/weights/best.pt  → copy to ai_engine/models/yolov8n_infrastructure.pt
"""

import argparse
from pathlib import Path


def main(data_yaml: str, epochs: int, imgsz: int, model_name: str, batch: int):
    from ultralytics import YOLO
    import ultralytics

    print(f"[NEXUS AI Detection Trainer]")
    print(f"  Base model  : {model_name}")
    print(f"  Dataset     : {data_yaml}")
    print(f"  Epochs      : {epochs}")
    print(f"  Image size  : {imgsz}")
    print(f"  Batch size  : {batch}")
    print()

    # Load base model (nano for CPU-fine MVP)
    model = YOLO(model_name)

    # Train
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name="nexus_infrastructure",
        project="./runs/detect",
        exist_ok=True,
        pretrained=True,
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        warmup_epochs=3,
        patience=30,          # early stopping after 30 epochs no improvement
        cos_lr=True,
        mosaic=1.0,
        mixup=0.1,
        copy_paste=0.1,
        augment=True,
        device="cpu",         # change to 0 for GPU
        workers=4,
        save_period=10,
        val=True,
        plots=True,
    )

    # Evaluate
    metrics = model.val()
    print("\n── Validation Metrics ──────────────────────────────────")
    print(f"  mAP50      : {metrics.box.map50:.4f}")
    print(f"  mAP50-95   : {metrics.box.map:.4f}")
    print(f"  Precision  : {metrics.box.mp:.4f}")
    print(f"  Recall     : {metrics.box.mr:.4f}")

    # Export ONNX for production inference (lighter, faster)
    onnx_path = model.export(format="onnx", imgsz=imgsz, simplify=True)
    print(f"\n  ONNX export: {onnx_path}")

    # Copy best weights to models dir
    best_pt = Path("runs/detect/nexus_infrastructure/weights/best.pt")
    dest = Path(__file__).parent.parent / "models" / "yolov8n_infrastructure.pt"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if best_pt.exists():
        import shutil
        shutil.copy2(best_pt, dest)
        print(f"  Best model saved → {dest}")

    print("\n[DONE] Training complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data",    default="./datasets/infrastructure_yolo/data.yaml")
    parser.add_argument("--epochs",  type=int, default=100)
    parser.add_argument("--imgsz",   type=int, default=640)
    parser.add_argument("--model",   default="yolov8n.pt")
    parser.add_argument("--batch",   type=int, default=8)
    args = parser.parse_args()
    main(args.data, args.epochs, args.imgsz, args.model, args.batch)
