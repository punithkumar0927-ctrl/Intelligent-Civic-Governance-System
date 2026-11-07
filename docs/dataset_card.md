# NEXUS AI — Dataset Card

## 1. Overview

| Field | Value |
|---|---|
| **Dataset Name** | NEXUS Infrastructure Defect Dataset (NIDD) |
| **Primary Use** | YOLOv8 detection training + severity model |
| **Collection Period** | 2024–2025 |
| **Total Images** | ~8,000–12,000 (composed from public datasets) |
| **Licenses** | Mixed — see sub-datasets below |
| **Format** | YOLO txt annotation format |

---

## 2. Constituent Public Datasets

### 2.1 RDD2022 (Road Damage Detection 2022)
- **Source**: https://github.com/abderyu/RDD2022
- **Paper**: "RDD2022: Large-scale Road Damage Dataset" (ICPR 2022)
- **Location**: Japan, India, Czech Republic, USA, Norway
- **Size**: 8,000+ images, 22 damage classes
- **License**: CC-BY-NC-SA 4.0 (non-commercial research)
- **Classes Used**: pothole, longitudinal_crack, transverse_crack, alligator_crack
- **Limitations**:
  - Mostly dashcam/vehicle-mounted viewpoint (not pedestrian-level like citizen reports)
  - Some scenes have Asian road markings different from Indian municipal context
  - License restricts commercial use — requires re-licensing for product deployment

### 2.2 RDD2020 (Global Road Damage Detection Challenge)
- **Source**: https://github.com/abderyu/RDD2020
- **Size**: 55,544 images, 3 task regions (Japan, India, Czech/USA/Norway)
- **License**: Apache 2.0
- **Classes Used**: dp (diamond cracking), pn (pot hole), mf (multiple cracking), etc.
- **Limitations**: Similar viewpoint bias as RDD2022; India subset is only 10.6% of data

### 2.3 Roboflow Pothole Datasets (Community)
- **Source**: https://universe.roboflow.com (search "pothole")
- **Notable**: "Pothole Detection v5" (~3,600 images), "Road Damage Detection" (~1,900 images)
- **License**: CC-BY-4.0 (per dataset — verify each)
- **Limitations**:
  - Annotator quality varies (some single-annotator projects)
  - Class definitions not standardized across datasets
  - Some images scraped from web — provenance uncertain

### 2.4 TDD (Teton Data Drive) — Pothole dataset
- **Source**: Kaggle / public domain (WyomingDOT)
- **Size**: ~1,200 annotated pothole frames
- **License**: Public domain (US government)

### 2.5 Synthetic severity training data
- **Method**: Python numpy simulation (`ai_engine/severity/train.py --synthetic`)
- **Size**: 5,000 synthetic samples
- **Purpose**: Initial XGBoost severity model training
- **Limitations**: Does NOT reflect real-world distribution. Must be replaced
  with actual labelled reports from deployed system within 30 days of launch.

### 2.6 Nominatim / OSM Geodata
- **Source**: https://nominatim.org, https://download.geofabrik.de
- **Use**: Reverse geocoding, ward boundary mapping
- **License**: ODbL (Open Data Commons Open Database License)

---

## 3. Annotation Schema (YOLO format)

```
<class_id> <x_center> <y_center> <width> <height>   (all normalized 0–1)
```

**Class IDs**:
```
0  = pothole
1  = crack
2  = garbage
3  = damaged_sidewalk
4  = broken_streetlight
5  = water_leak
6  = blocked_drain
7  = damaged_road
8  = overgrown
9  = broken_sign
```

**Data YAML** (`datasets/infrastructure_yolo/data.yaml`):
```yaml
path: ./datasets/infrastructure_yolo
train: images/train
val:   images/val
names:
  0: pothole
  1: crack
  2: garbage
  3: damaged_sidewalk
  4: broken_streetlight
  5: water_leak
  6: blocked_drain
  7: damaged_road
  8: overgrown
  9: broken_sign
```

---

## 4. Data Preprocessing Pipeline

```
Raw images
    │
    ├─ Deduplication (phash Hamming distance ≤ 5)
    ├─ EXIF GPS extraction (optional location labels)
    ├─ Format standardization → JPEG 640x640 (max side)
    ├─ Annotation format conversion → YOLO txt
    ├─ Class merging (RDD2022 damage types → NEXUS 10 classes)
    ├─ Train/Val/Test split (70/20/10, stratified by class)
    └─ Augmentation flags:
        ├─ Mosaic (1.0 probability)
        ├─ Mixup (0.1)
        ├─ Copy-paste (0.1)
        ├─ HSV jitter
        └─ Random flip + rotation ±10°
```

---

## 5. Severity Model Dataset

**Target variable**: 4-class ordinal (LOW=0, MEDIUM=1, HIGH=2, CRITICAL=3)

**Feature engineering**:
| Feature | Source | Range |
|---|---|---|
| `cat_enc` | Category base risk (domain expert) | 0.0–1.0 |
| `confidence` | YOLO model output | 0.0–1.0 |
| `edge_density` | Canny edge / total pixels | 0.0–1.0 |
| `contrast` | Std of grayscale / 255 | 0.0–1.0 |
| `damage_area_ratio` | Edge proxy for damage region | 0.0–1.0 |
| `has_critical_kw` | Description keyword match | 0 or 1 |
| `upvotes_log` | log1p(upvotes) / log1p(100) | 0.0–1.0 |

**Current dataset**: 5,000 synthetic samples (placeholder).
**Required**: Minimum 2,000 real labelled reports before production deployment.
Labelling protocol: 3 domain expert raters + inter-rater reliability (Cohen's Kappa ≥ 0.7).

---

## 6. Ethical & Bias Considerations

### 6.1 Geographic Bias
Most public road-damage datasets are from Japan, USA, and Europe.
Indian municipal contexts (monsoon damage, auto-rickshaw scale, colonial-era
infrastructure) are underrepresented. **Mitigation**: Prioritize RDD India subset
and plan 500+ manually captured Indian citizen photos before model freeze.

### 6.2 Socioeconomic Bias
Neighborhoods with more smartphone users will report more issues.
This correlates with income — low-income areas may be underdetected.
**Mitigation**: Track per-ward report density vs. census data.

### 6.3 Privacy
EXIF GPS coordinates can identify reporters. We:
- Strip EXIF from uploaded images server-side
- Round published coordinates to 3 decimal places (~111m)
- Never expose reporter phone numbers or emails publicly

### 6.4 Model Harm
A false "low severity" on a critical hazard could delay repair.
**Mitigation**:
- Conservative threshold bias (slightly over-flag rather than under-flag)
- All CRITICAL alerts require human confirmation before automated escalation
- Public confidence display on all AI labels (transparency)

---

## 7. Known Limitations

1. **RDD datasets are dashcam-view** — citizen phone images (angled, close-up)
   may reduce mAP by 10–20% until domain-adapted fine-tuning is done.
2. **No audio or video processing** in current MVP — multimodal pipeline
   designed but not yet implemented (Phase 2 roadmap).
3. **Synthetic severity training data** is a temporary proxy. Model will
   underperform real-world distribution until retrained with actual reports.
4. **Class imbalance**: pothole samples likely 5x more frequent than power_line
   or building_defect in all public datasets. Use class-weighted loss or
   oversampling during fine-tuning.
5. **Indian road scenes** lack large annotated datasets specifically for
   municipal issues (garbage piles, open manholes, illegal dumping) beyond
   what RDD2022 India provides. Community-contributed data needed.

---

## 8. Citation

If you use NEXUS AI components in research, please cite the source datasets:

```bibtex
@inproceedings{maeda2022rdd,
  title={RDD2022: Five-region, Large-scale Road Damage Dataset},
  author={Maeda, Soren and Sekimoto, Yusuke and Seto, Takumi and others},
  booktitle={Proceedings of ICPR},
  year={2022}
}
```
