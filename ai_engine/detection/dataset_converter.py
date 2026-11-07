"""Convert an RDD2022-style folder into YOLO label files when the dataset is present."""

from pathlib import Path
import argparse
import xml.etree.ElementTree as ET

# RDD2022 class ids used by this project.
CLASS_IDS = {
    "D00": 0,  # longitudinal crack
    "D10": 1,  # transverse crack
    "D20": 2,  # alligator crack
    "D40": 3,  # pothole
}


def convert_xml_file(xml_path: Path, out_dir: Path) -> int:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    size = root.find("size")
    if size is None:
        return 0
    width = float(size.findtext("width") or 0)
    height = float(size.findtext("height") or 0)
    if width <= 0 or height <= 0:
        return 0
    lines = []
    for obj in root.findall("object"):
        name = (obj.findtext("name") or "").strip()
        if name not in CLASS_IDS:
            continue
        box = obj.find("bndbox")
        if box is None:
            continue
        xmin = float(box.findtext("xmin") or 0)
        ymin = float(box.findtext("ymin") or 0)
        xmax = float(box.findtext("xmax") or 0)
        ymax = float(box.findtext("ymax") or 0)
        cx = ((xmin + xmax) / 2) / width
        cy = ((ymin + ymax) / 2) / height
        bw = (xmax - xmin) / width
        bh = (ymax - ymin) / height
        lines.append(f"{CLASS_IDS[name]} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{xml_path.stem}.txt").write_text("\n".join(lines), encoding="utf-8")
    return len(lines)


def convert_directory(source: Path, destination: Path) -> dict:
    if not source.exists():
        return {
            "status": "DATASET_NOT_PRESENT",
            "message": (
                "RDD2022 was not found at the given path. "
                "See https://doi.org/10.6084/m9.figshare.21431547.v1 and place the extracted files locally."
            ),
            "converted": 0,
        }
    xml_files = list(source.rglob("*.xml"))
    boxes = 0
    for xml_path in xml_files:
        boxes += convert_xml_file(xml_path, destination)
    return {"status": "converted", "files": len(xml_files), "boxes": boxes, "destination": str(destination)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--destination", default="datasets/road_damage/labels")
    args = parser.parse_args()
    print(convert_directory(Path(args.source), Path(args.destination)))
