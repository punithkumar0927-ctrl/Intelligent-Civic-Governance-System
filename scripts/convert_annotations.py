"""
scripts/convert_annotations.py
Converts COCO JSON or Pascal VOC XML to YOLO darknet txt format.
Usage:
  python convert_annotations.py coco <coco.json> <images_dir> <labels_dir>
  python convert_annotations.py voc <voc_dir> <images_dir> <labels_dir> <class1,class2,...>
  python convert_annotations.py split <src_dir> <train_dst> <val_dst> <test_dst> [ratio=0.8]
"""
import json, sys, shutil
from pathlib import Path
from xml.etree import ElementTree as ET


def convert_coco(coco_json: str, images_dir: str, labels_dir: str):
    with open(coco_json) as f:
        coco = json.load(f)
    cat_map = {c["id"]: i for i, c in enumerate(coco["categories"])}
    ann_by_img: dict = {}
    for ann in coco["annotations"]:
        ann_by_img.setdefault(ann["image_id"], []).append(ann)
    Path(labels_dir).mkdir(parents=True, exist_ok=True)
    for img_info in coco["images"]:
        stem = Path(img_info["file_name"]).stem
        w, h = img_info["width"], img_info["height"]
        lines = []
        for ann in ann_by_img.get(img_info["id"], []):
            x, y, bw, bh = ann["bbox"]
            cls = cat_map[ann["category_id"]]
            cx, cy = (x + bw/2)/w, (y + bh/2)/h
            nw, nh = bw/w, bh/h
            lines.append(f"{cls} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")
        if lines:
            with open(Path(labels_dir)/f"{stem}.txt", "w") as f:
                f.write("\n".join(lines))
    print(f"[coco->yolo] {len(coco['images'])} images -> {labels_dir}")


def convert_voc(voc_dir: str, images_dir: str, labels_dir: str, class_list_str: str):
    class_list = class_list_str.split(",")
    cat_idx = {c: i for i, c in enumerate(class_list)}
    Path(labels_dir).mkdir(parents=True, exist_ok=True)
    count = 0
    for xml_path in Path(voc_dir).glob("*.xml"):
        root = ET.parse(str(xml_path)).getroot()
        size = root.find("size")
        w = int(size.findtext("width", 640)); h = int(size.findtext("height", 640))
        lines = []
        for obj in root.findall("object"):
            name = obj.findtext("name", "").strip()
            if name not in cat_idx: continue
            bb = obj.find("bndbox")
            x1=float(bb.findtext("xmin",0)); y1=float(bb.findtext("ymin",0))
            x2=float(bb.findtext("xmax",0)); y2=float(bb.findtext("ymax",0))
            cx,cy = (x1+x2)/2/w, (y1+y2)/2/h
            nw,nh = (x2-x1)/w, (y2-y1)/h
            lines.append(f"{cat_idx[name]} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")
        with open(Path(labels_dir)/f"{xml_path.stem}.txt", "w") as f:
            f.write("\n".join(lines))
        count += 1
    print(f"[voc->yolo] {count} XML -> {labels_dir}")


def split_dataset(src_dir: str, dst_train: str, dst_val: str, dst_test: str, ratio: float = 0.8):
    import random
    files = list(Path(src_dir).glob("*.jpg")) + list(Path(src_dir).glob("*.png"))
    random.shuffle(files)
    n = len(files); t = int(n*ratio); v = int(n*(1-ratio)*0.5)
    for d in [dst_train, dst_val, dst_test]:
        Path(d).mkdir(parents=True, exist_ok=True)
    for i, f in enumerate(files):
        dst = dst_train if i < t else (dst_val if i < t+v else dst_test)
        shutil.copy2(f, Path(dst)/f.name)
    print(f"[split] train={t}, val={v}, test={n-t-v}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "coco": convert_coco(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "voc": convert_voc(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    elif cmd == "split": split_dataset(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else: print(__doc__)
