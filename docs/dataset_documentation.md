# NEXUS AI - Dataset Documentation

## Primary Datasets

### RDD2022 – Road Damage Detection (2022)
- **Source**: https://rdd2022.in
- **Licence**: CC BY 4.0 (free for research and commercial use with attribution)
- **Location**: India (12 cities)
- **Format**: COCO JSON + original images
- **Size**: ~22,000 images; 5 damage classes
- **Resolution**: ~960×540 (phone/dashcam)
- **Conversion**: COCO → YOLO txt via `scripts/convert_annotations.py`

### Garbage-Net
- **Source**: https://github.com/garbage-net
- **Licence**: MIT
- **Classes**: plastic, paper, metal, e-waste, organic
- **Format**: Pascal VOC XML → YOLO txt

### CPHEEO Severity Labels (Internal)
- Annotated by 3 civic engineers with 5+ years municipal experience
- 5-point scale collapsed to 4 severity classes
- Inter-annotator agreement: Cohen's kappa (to be measured)
- Used exclusively for XGBoost severity training

### OSM Bengaluru Extract
- **Source**: Geofabrik (https://download.geofabrik.de)
- **Licence**: ODbL (Open Data Commons Open Database Licence)
- **Content**: Road network, amenities (schools, hospitals, etc.), ward boundaries
- **Format**: .pbf → filtered to road_networks/ and osm_data/ subdirectories
- **Update frequency**: Monthly

## Storage Structure

```
datasets/
├── road_damage/          ← RDD2022 (primary detection)
│   ├── raw/              ← Original downloads
│   ├── images/{train,val,test}/
│   ├── labels/{train,val,test}/
│   └── data.yaml
├── resolution_verification/
│   ├── before/           ← Before-repair photos
│   ├── after/            ← After-repair photos
│   └── *.csv             ← Pair indices + labels
├── geographic_intelligence/
│   ├── osm_data/         ← Raw OSM files
│   ├── road_networks/    ← Processed road segments
│   └── *.csv             ← Location metadata
└── dataset_registry.csv  ← Master registry
```

## Data Quality Requirements
1. Every image must have a valid label file in YOLO format
2. Bounding boxes: all values in [0, 1]; class IDs in [0, nc-1]
3. Run `scripts/validate_dataset.py` before training
4. Keep raw downloads in `raw/` separate from processed data
5. Never overwrite originals – processed copies only

## Preprocessing Pipeline
```
Raw image → CLAHE contrast → 640×640 resize → [augment HSV] → sharpen → YOLO format
```

## Dataset Registry
See `datasets/dataset_registry.csv` for complete metadata including source URL, licence, version, sample count, format, and preprocessing details for each dataset.
