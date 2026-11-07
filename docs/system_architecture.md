# NEXUS AI - System Architecture

## High-Level Components

```
[Frontend: React SPA]
       |  HTTPS + JWT
[API Gateway: FastAPI]
  ├── /auth          → JWT issue/verify
  ├── /reports       → CRUD + file upload
  ├── /analytics     → Summary statistics
  ├── /geographic    → Hotspots, ward reports, nearby
  └── /verification  → Before/after AI comparison
       |
[Service Layer]
  ├── vision_service      → YOLOv8 inference
  ├── severity_service    → XGBoost scoring
  ├── duplicate_service   → FAISS + dHash
  ├── geographic_service  → DBSCAN + PostGIS
  ├── verification_service→ SSIM pipeline
  └── report_service      → Report text generation
       |
[Data Layer]
  ├── PostgreSQL + PostGIS  → Issues, users, locations
  ├── Local filesystem      → Uploaded images
  └── FAISS index (in-mem)  → Text embedding search
       |
[AI Engine (ai_engine/)]
  ├── detection/            → YOLOv8 training + prediction
  ├── severity/             → XGBoost feature extraction
  ├── geographic_intelligence/ → OSM, GPS, clustering
  ├── resolution_verification/ → Image alignment + SSIM
  ├── duplicate_detection/  → dHash + embeddings
  └── generative_ai/        → Standards-based reports
```

## Request Flow: Issue Report

```
1. Citizen uploads photo + GPS + description
2. file_handler.py validates MIME type and size (max 20MB)
3. image_processor.py strips EXIF, saves UUID-named file
4. vision_service.py runs YOLOv8 → detected_label + confidence
5. severity_service.py extracts features → XGBoost → severity
6. duplicate_service.py checks dHash + FAISS index
7. geographic_service.py queries OSM → road name, ward, risk
8. Issue saved to PostgreSQL with all AI metadata
9. Location saved to locations table with OSM fields
10. Report generated via report_service.py (standards text)
```

## Security Architecture

| Layer | Control |
|---|---|
| Authentication | JWT bearer token; 8-hour expiry; bcrypt passwords |
| Authorization | Role hierarchy: citizen(0) < officer(1) < admin(2) |
| File uploads | MIME whitelist; 20MB limit; UUID filename |
| EXIF privacy | GPS EXIF stripped on all uploads |
| Coordinate display | Rounded to 3 decimal places (~111m) |
| API rate limit | (Planned: nginx limit_req; per-IP) |
| Input validation | Pydantic schemas; coordinate range check |

## Database Schema

See `docs/database_design.md` for full schema.

## Scaling Considerations

- YOLOv8 inference: batch images via a background task queue (Celery + Redis)
- FAISS index: rebuild nightly; keep in worker process memory
- OSM queries: cache Nominatim results; refresh monthly
- PostgreSQL: add PostGIS GiST indexes; partition issues by city
- Frontend: serve static files via CDN; API calls cached via TanStack Query
