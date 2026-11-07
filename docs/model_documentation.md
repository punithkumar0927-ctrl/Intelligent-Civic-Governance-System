# NEXUS AI - Model Documentation

## 1. Road Damage Detection (YOLOv8n)

**Architecture**: YOLOv8n (nano) – 3.2M parameters  
**Base model**: Ultralytics yolov8n.pt (COCO pre-trained)  
**Fine-tuned on**: RDD2022 (Indian road damage images)  
**Input size**: 640×640 RGB  
**Output**: Bounding boxes with class labels and confidence scores

### Classes
| ID | Class | Description |
|---|---|---|
| 0 | medium_damaged | Surface cracking, minor depression |
| 1 | severely_damaged | Deep potholes, road collapse |
| 2 | unpaved | Gravel/unmaintained road surface |
| 3 | longitudinal_transverse_crack | Linear cracks along/across road |
| 4 | alligator_crack | Interconnected fatigue cracking pattern |

### Performance (on RDD2022 val set)
| Metric | Pretrained (COCO) | Fine-tuned (RDD2022) |
|---|---|---|
| mAP50-95 | ~0.18 | ~0.42 (expected) |
| mAP50 | ~0.30 | ~0.62 (expected) |
| Inference time (CPU) | ~200ms | ~220ms |
| Model size | 6.3 MB | 6.5 MB |

*Actual values depend on fine-tuning. Placeholder until full training completed.*

### File
`ai_engine/models/detection/yolov8n_rdd2022.pt`

---

## 2. Severity Prediction (XGBoost)

**Type**: Multi-class gradient boosted tree  
**Classes**: LOW / MEDIUM / HIGH / CRITICAL  
**Features**: 13 visual + contextual features (see feature_extraction.py)  
**Training data**: `datasets/severity_prediction/severity_data.csv`  
**Model size**: ~50 KB (JSON format)

### Features
| Feature | Type | Source |
|---|---|---|
| edge_density | float | Canny edges / total pixels |
| dark_ratio | float | Pixels < 60 gray / total |
| texture_variance | float | Std(gray) / 255 |
| damage_area_pct | float | Sum(bbox areas) / image area |
| bbox_count | int | Number of YOLO detections |
| mean_confidence | float | Avg YOLO confidence |
| brightness_mean | float | Mean gray 0-255 |
| contrast_range | int | p95 - p5 of gray values |
| aspect_ratio | float | Avg bbox W/H |
| weather | int | 0=clear, 1=rain, 2=fog |
| road_type | int | 0=residential, 1=arterial, 2=highway |
| traffic_level | int | 0=low, 1=medium, 2=high |
| image_area_megapixels | float | Resolution proxy |

### Severity Decision Thresholds
| Model Score | Severity | SLA (hours) |
|---|---|---|
| ≥ 0.75 | CRITICAL | 24h |
| 0.50–0.74 | HIGH | 72h |
| 0.25–0.49 | MEDIUM | 168h (7d) |
| < 0.25 | LOW | 336h (14d) |

### Fallback (heuristic baseline)
`score = 0.4*edge_density + 0.35*dark_ratio + 0.25*(damage_area*10)`

---

## 3. Text Embedding (Sentence-Transformers)

**Model**: all-MiniLM-L6-v2  
**Dimensions**: 384  
**Max tokens**: 256  
**Use**: Semantic similarity for duplicate text detection  
**Inference**: ~10ms per text on CPU  
**Storage**: FAISS IndexFlatIP in backend process memory

---

## 4. Image Perceptual Hash (dHash)

**Method**: Difference hash 16×16 → 256-bit binary string  
**Comparison**: Hamming distance → similarity = 1 - dist/256  
**Threshold**: ≥0.80 (≤51 differing bits) = probable duplicate  
**Inference**: ~5ms per image (OpenCV resize + compare)  
**No model file required** – implemented in pure OpenCV

---

## 5. Repair Verification (SSIM + Edge Density)

**Pipeline**: ORB alignment → SSIM → edge density comparison → composite score  
**Resolved probability formula**:
```
base = 0.5 * edge_reduction + 0.5 * damage_reduction
if SSIM > 0.90: base *= 0.2  (nothing changed)
if hue_drift > 30: base *= 0.4 (different scene penalty)
probability = min(base + 0.15, 1.0)
```

**Thresholds**:
| Probability | Status |
|---|---|
| ≥ 0.75 | LIKELY_FIXED |
| ≥ 0.55 | PARTIALLY_FIXED |
| ≥ 0.35 | NEEDS_REVIEW |
| < 0.35 | NOT_FIXED |

### Known Limitations
- Works best with similar camera angles; large perspective changes reduce accuracy
- Shadows and lighting differences can cause false NOT_FIXED verdicts
- Partial repairs may be classified as NOT_FIXED if patch area is small vs. total image
- Human review queue handles ambiguous cases
