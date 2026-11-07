# NEXUS AI - Project Overview

## What Is NEXUS AI?

NEXUS AI is an open-source civic infrastructure intelligence platform that uses computer vision, machine learning, and geographic data to understand, classify, and track real-world urban problems from citizen-submitted photos and text reports.

## Core Capabilities

| Capability | Model/Method | Output |
|---|---|---|
| Road damage detection | YOLOv8n fine-tuned on RDD2022 | Bounding boxes + class labels |
| Damage severity prediction | XGBoost classifier | LOW / MEDIUM / HIGH / CRITICAL |
| Duplicate issue detection | dHash + sentence-transformers + geo | Similarity score 0-1 |
| Repair verification | SSIM + edge density comparison | Fixed / Partially / Not Fixed |
| Geographic hotspot analysis | DBSCAN clustering | Hotspot risk score |
| Action recommendations | Knowledge-base lookup (IRC/CPHEEO/SWM) | Prioritised step list |

## Novel Contributions

1. **Multi-signal composite duplicate scoring**: Combining perceptual image hash, semantic text embedding, geographic proximity, and category match in one weighted score is not implemented in any known open-source civic platform.
2. **Evidence-grounded recommendations**: All action items cite specific clauses from Indian municipal engineering standards (IRC:73-2018, CPHEEO Manual, SWM Rules 2016). The system never uses a generative LLM to fabricate solutions.
3. **Conservative severity bias**: When the model is uncertain, it favours over-flagging (higher severity) rather than under-flagging, ensuring critical issues are never missed.
4. **Repair verification pipeline**: ORB-based homography alignment followed by SSIM + edge density comparison with calibrated thresholds and a human-review queue for ambiguous cases.

## Competitive Landscape

| Platform | CV Detection | Severity ML | Duplicate AI | Geo Hotspots | Open Source | Standards-Cited |
|---|---|---|---|---|---|---|
| FixMyStreet (UK) | No | No | No | Basic | Yes | No |
| SeeClickFix (US) | No | No | Manual | Basic | No | No |
| Mark-a-Spot (DE) | No | No | Manual | Basic | No | No |
| IWatchRoad (IN) | No | No | No | No | No | No |
| **NEXUS AI** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** |

NEXUS AI is the only open-source platform combining all six capabilities.

## Technical Architecture

```
Citizen Browser
      |
  React 18 + TypeScript + Vite (port 5173)
      |
  FastAPI (port 8000)
      |
  +------+------+------+
  |      |      |      |
YOLO  XGBoost  FAISS  OSM
  |      |      |      |
  +------+------+------+
         |
  PostgreSQL + PostGIS (port 5432)
```

## Deployment Options

- **Local**: `docker-compose up` (PostgreSQL + FastAPI + React)
- **Cloud**: Any VM with Docker; or FastAPI behind nginx
- **Offline field kit**: YOLOv8n + XGBoost model files; works without internet

## Limitations

- Detection accuracy depends on camera angle and lighting
- Severity model requires human-labelled training data
- OSM data availability varies by city and may be incomplete
- Repair verification is unreliable for very different camera angles
- Not validated as a legal or safety certification tool
