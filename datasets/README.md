# Datasets — NEXUS AI

This directory holds every dataset used for model training, evaluation, and the
geographic intelligence layer. The structure below mirrors
`docs/dataset_documentation.md`.

> **Rule 4 (from project spec):** Every dataset must be recorded in
> `dataset_registry.csv` with its source, licence, version, and preprocessing
> details before it is used for training.

---

## Directory Layout

```
datasets/
├── dataset_registry.csv          ← master provenance table (9 entries)
│
├── road_damage/                  ← RDD2022 primary detection dataset
│   ├── raw/                      ← Original downloads – never modify
│   ├── images/
│   │   ├── train/                ← 80 % split (YOLO format)
│   │   ├── val/                  ← 10 % split
│   │   └── test/                 ← 10 % split
│   ├── labels/
│   │   ├── train/
│   │   ├── val/
│   │   └── test/
│   └── data.yaml                 ← YOLO config: 5 damage classes
│
├── garbage_detection/            ← Garbage-Net (MIT licence)
│   ├── images/                   ← Train/val/test JPGs
│   ├── annotations/              ← Original Pascal VOC XML files
│   └── data.yaml                 ← YOLO config: 6 waste classes
│
├── flood_detection/              ← FloodNet waterlogging scenes
│   ├── images/
│   └── annotations/
│
├── urban_accessibility/          ← Field-collected footpath hazard photos
│   ├── images/
│   ├── annotations/
│   └── metadata.csv              ← GPS + severity + issue type per image
│
├── resolution_verification/      ← Before/after repair photo pairs
│   ├── before/                   ← Original damage photographs
│   ├── after/                    ← Post-repair photographs
│   ├── image_pairs/              ← Aligned side-by-side composites
│   ├── before_after_pairs.csv    ← Issue ID, paths, repair method, date
│   └── verification_labels.csv   ← Ground-truth RESOLVED/PARTIAL/NOT_RESOLVED
│
├── geographic_intelligence/      ← OSM and GPS data
│   ├── osm_data/                 ← .pbf / .shp extracts from Geofabrik
│   ├── road_networks/            ← Road segments for matcher
│   ├── gps_records/              ← Raw GPS traces from field collection
│   ├── road_locations.csv        ← Road segment ID, name, coordinates
│   ├── issue_coordinates.csv     ← Issue ID, lat, lon, ward
│   └── geographic_metadata.csv   ← Risk score, landmark, nearby amenities
│
├── severity_prediction/
│   └── severity_data.csv         ← 13-feature XGBoost training rows
│
└── duplicate_detection/
    └── image_pairs.csv           ← Pair ID, similarity label, image paths
```

---

## 1. Road Damage Detection — RDD2022

**Primary detection dataset.** Contains 22 000+ street-level images from Indian
cities with five damage classes annotated in YOLO format.

| Field | Value |
|---|---|
| Source | https://rdd2022.in |
| Licence | CC BY 4.0 |
| Classes | `medium_damaged`, `severely_damaged`, `unpaved`, `longitudinal_transverse_crack`, `alligator_crack` |
| Split | 80 / 10 / 10 (train / val / test) |
| Image size | 640 × 640 |
| Preprocessing | CLAHE contrast boost; HSV augmentation; EXIF stripped |

**Download steps:**
```bash
# Clone the official RDD2022 repository
git clone https://github.com/abderyu/RDD2022 datasets/road_damage/raw

# Convert and split into YOLO layout
python scripts/convert_annotations.py --source rdd2022 --out datasets/road_damage/

# Verify integrity
python scripts/validate_dataset.py --data datasets/road_damage/data.yaml
```

---

## 2. Garbage Detection — Garbage-Net

| Field | Value |
|---|---|
| Source | https://github.com/drgutoss/Garbage-Net |
| Licence | MIT |
| Classes | `plastic`, `paper`, `cardboard`, `glass`, `e_waste`, `organic_waste` |
| Images | ~8 500 |
| Format | Pascal VOC XML → YOLO txt |

```bash
python scripts/convert_annotations.py --source voc --in datasets/garbage_detection/annotations --out datasets/garbage_detection/images
```

---

## 3. Flood Detection — FloodNet

| Field | Value |
|---|---|
| Source | https://data.mendeley.com/ (FloodNet) |
| Licence | CC BY 4.0 |
| Classes | `waterlogging`, `flood_building`, `flood_road`, `debris` |
| Images | ~4 200 |

Place images in `flood_detection/images/` and YOLO labels in
`flood_detection/annotations/`.

---

## 4. Urban Accessibility — Field Collection

Bengaluru-specific footpath hazard dataset with GPS coordinates captured per
image. See `metadata.csv` for the full column schema.

| Column | Description |
|---|---|
| `image_id` | Unique identifier |
| `accessibility_issue` | `blocked_footpath` / `missing_ramp` / `uneven_pavement` / `drain_cover_missing` / `obstructed_path` |
| `severity` | 1 = low · 4 = critical |
| `latitude`, `longitude` | GPS to 4 decimal places |

---

## 5. Resolution Verification — Before/After Pairs

| File | Content |
|---|---|
| `before_after_pairs.csv` | `pair_id, issue_id, before_path, after_path, repair_method, before_date, after_date` |
| `verification_labels.csv` | `pair_id, ground_truth_label` (RESOLVED / PARTIAL_RESOLVED / NOT_RESOLVED) |

Place original photos in `before/` and `after/`. Aligned composites go in
`image_pairs/`.

---

## 6. Geographic Intelligence — OSM Bengaluru

| File | Content |
|---|---|
| `road_locations.csv` | `road_id, road_name, ward, lat_start, lon_start, lat_end, lon_end` |
| `issue_coordinates.csv` | `issue_id, latitude, longitude, ward` |
| `geographic_metadata.csv` | `issue_id, risk_score, landmark_name, nearby_schools, nearby_hospitals` |

OSM extracts can be downloaded from Geofabrik:
```
https://download.geofabrik.de/asia/india/karnataka-state/
```
Place the `.pbf` or `.shp` files in `osm_data/`.

---

## 7. Severity Prediction

`severity_data.csv` contains one row per annotated image with 13 feature columns
and a `severity` label. Features are generated by:
```bash
python ai_engine/severity/feature_extraction.py --batch datasets/road_damage/images/train
```

---

## 8. Duplicate Detection

`image_pairs.csv` stores labelled pairs for evaluation:
```csv
pair_id,image_a,image_b,is_duplicate,similarity_score
dup_001,rdd_001.jpg,rdd_017.jpg,1,0.92
```

---

## Important Notes

- **DO NOT commit large image files to Git.** Add dataset image paths to
  `.gitignore`.
- **Raw data is immutable.** Place original downloads in `raw/` subdirectories.
- **Licence check before deployment.** CC-BY-NC datasets cannot be used in
  commercial products without re-licensing.
- **Dataset registry is the source of truth** for provenance. Update
  `dataset_registry.csv` whenever a new dataset is added.

---

## Indian Context Data Collection

To improve model accuracy on local municipal scenes:

1. Photograph 100–500 local infrastructure issues with geotagging enabled
2. Annotate in [Roboflow](https://roboflow.com) (free tier: 200 images/month) or LabelImg
3. Export in YOLOv8 format; place in `road_damage/images/train/` and `labels/train/`
4. Retrain:
   ```bash
   python ai_engine/detection/train.py --data datasets/road_damage/data.yaml --epochs 50
   ```
