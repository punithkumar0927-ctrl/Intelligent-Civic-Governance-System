"""
scripts/download_datasets.py
Downloads and prepares the RDD2022 road-damage dataset for YOLOv8 training.
Only downloads public, freely licensed data.
"""
import os
import sys
import urllib.request
import zipfile
import shutil
from pathlib import Path

BASE = Path(__file__).parent.parent
DATASET_DIR = BASE / "datasets" / "road_damage"
IMAGES_TRAIN = DATASET_DIR / "images" / "train"
IMAGES_VAL = DATASET_DIR / "images" / "val"
LABELS_TRAIN = DATASET_DIR / "labels" / "train"
LABELS_VAL = DATASET_DIR / "labels" / "val"


def ensure_dirs():
    for d in [IMAGES_TRAIN, IMAGES_VAL, LABELS_TRAIN, LABELS_VAL]:
        d.mkdir(parents=True, exist_ok=True)


def download_file(url: str, dest: Path, desc: str = "") -> bool:
    if dest.exists():
        print(f"[skip] Already downloaded: {dest.name}")
        return True
    print(f"[download] {desc or url}")
    try:
        urllib.request.urlretrieve(url, str(dest))
        print(f"[done] -> {dest}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to download {url}: {e}")
        return False


def placeholder_mode():
    """
    Creates small synthetic sample images so the pipeline can be tested
    without downloading the full 4 GB RDD2022 dataset.
    """
    import numpy as np
    print("\n[PLACEHOLDER MODE] Creating synthetic sample data for pipeline testing...")
    ensure_dirs()

    for split, img_dir, lbl_dir in [
        ("train", IMAGES_TRAIN, LABELS_TRAIN),
        ("val", IMAGES_VAL, LABELS_VAL),
    ]:
        for i in range(20):
            try:
                from PIL import Image
                arr = (np.random.rand(640, 640, 3) * 200 + 28).astype("uint8")
                Image.fromarray(arr).save(img_dir / f"sample_{i:04d}.jpg", "JPEG")
            except ImportError:
                # Minimal JPEG bytes (smallest valid JPEG ~1KB)
                (img_dir / f"sample_{i:04d}.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)

            with open(lbl_dir / f"sample_{i:04d}.txt", "w") as f:
                f.write("0 0.500000 0.500000 0.200000 0.150000\n")
                f.write("1 0.300000 0.700000 0.100000 0.100000\n")

        print(f"[placeholder] Created 20 samples for '{split}' split")

    print("\nDone! Replace placeholder images with real RDD2022 data for actual training.")
    print("Run with 'full' argument to attempt real download: python download_datasets.py full")


def full_mode():
    """
    Attempt to download RDD2022 from the official source.
    NOTE: RDD2022 requires registration at https://rdd2022.in — this script
    does NOT bypass that. Users must obtain their own download links.
    """
    print("=== RDD2022 Full Dataset ===")
    print("RDD2022 is a free academic dataset. You must:")
    print("  1. Register at: https://rdd2022.in/")
    print("  2. Accept the data use agreement")
    print("  3. Download the train/test zips")
    print("  4. Place them in datasets/road_damage/raw/")
    print("  5. Run: python scripts/convert_annotations.py")
    print()
    print("For a pipeline test without downloading: python download_datasets.py placeholder")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "placeholder"
    ensure_dirs()
    if mode == "full":
        full_mode()
    elif mode == "validate":
        os.system(f"{sys.executable} scripts/validate_dataset.py")
    else:
        placeholder_mode()


if __name__ == "__main__":
    main()
