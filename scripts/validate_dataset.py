"""
scripts/validate_dataset.py
Validates YOLO dataset integrity: all images have labels, bboxes in [0-1],
classes < nc, no orphan label files.
"""
import sys, yaml
from pathlib import Path

DATASET_DIR = Path(__file__).parent.parent / "datasets" / "road_damage"


def validate_split(img_dir: Path, lbl_dir: Path, nc: int) -> dict:
    stats = {"total":0,"ok":0,"missing_lbl":0,"missing_img":0,"bad_bbox":0,"bad_class":0}
    imgs = {f.stem for f in list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png"))}
    lbls = {f.stem for f in lbl_dir.glob("*.txt")}
    for stem in imgs:
        stats["total"] += 1
        if stem not in lbls: stats["missing_lbl"] += 1; continue
        ok = True
        for line in (lbl_dir/f"{stem}.txt").read_text().splitlines():
            parts = line.strip().split()
            if len(parts) != 5: ok=False; stats["bad_bbox"]+=1; break
            try:
                cls=int(float(parts[0])); vals=[float(p) for p in parts[1:]]
                if not all(0<=v<=1 for v in vals): ok=False; stats["bad_bbox"]+=1; break
                if not 0<=cls<nc: ok=False; stats["bad_class"]+=1; break
            except ValueError: ok=False; stats["bad_bbox"]+=1; break
        if ok: stats["ok"] += 1
    stats["missing_img"] = len(lbls - imgs)
    return stats


def main():
    cfg_path = DATASET_DIR / "data.yaml"
    if not cfg_path.exists():
        print("data.yaml not found. Run: python scripts/download_datasets.py placeholder")
        sys.exit(1)
    with open(cfg_path) as f: cfg = yaml.safe_load(f)
    nc = cfg.get("nc", 5)
    print(f"Validating dataset at {DATASET_DIR} (nc={nc})")
    for split in ["train","val","test"]:
        key = cfg.get(split, f"images/{split}")
        img_d = DATASET_DIR / key
        lbl_d = DATASET_DIR / key.replace("images","labels")
        if not img_d.exists(): print(f"[{split}] Missing dir: {img_d}"); continue
        s = validate_split(img_d, lbl_d, nc)
        err = s["bad_bbox"]+s["bad_class"]
        print(f"[{split}] total={s['total']} ok={s['ok']} missing_lbl={s['missing_lbl']} "
              f"missing_img={s['missing_img']} bad_bbox={s['bad_bbox']} bad_class={s['bad_class']}"
              + (" <-- FIX THESE" if err else "  OK"))


if __name__ == "__main__":
    main()
