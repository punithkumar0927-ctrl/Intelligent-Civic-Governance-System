# NEXUS AI — System Architecture

## 1. High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                NEXUS AI SYSTEM                                   │
│                          The Living Intelligence Map                             │
└─────────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────┐          ┌──────────────────────────┐
  │   USER CLIENTS      │          │   MUNICIPAL DASHBOARD    │
  │  (React + Leaflet)  │          │   (officer/admin view)   │
  └────────┬────────────┘          └─────────────┬────────────┘
           │                                     │
           └──────────────────┬──────────────────┘
                              │  HTTPS / JWT Bearer
                   ┌──────────▼──────────┐
                   │   FastAPI Backend   │
                   │   (Python 3.11)     │
                   └──────────┬──────────┘
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
  ┌────────▼──────┐  ┌───────▼────────┐  ┌─────▼──────────┐
  │  Auth Service │  │ Report Service │  │  Analytics API │
  │  JWT + bcrypt│  │ CRUD + Upload  │  │  SQL + Charts  │
  └───────────────┘  └───────┬────────┘  └────────────────┘
                             │
                    ┌────────▼──────────────┐
                    │   AI PIPELINE ENGINE  │
                    └────────┬──────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
  ┌─────▼──────┐  ┌─────────▼────────┐  ┌──────▼────────┐
  │  VISION    │  │  SEVERITY        │  │  DUPLICATE    │
  │  YOLOv8n   │  │  XGBoost Model   │  │  FAISS +      │
  │  + OpenCV  │  │  + Rules Engine  │  │  ST Embeddings│
  └─────┬──────┘  └─────────┬────────┘  └──────┬────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                   ┌────────▼─────────────┐
                   │  RECOMMENDATION      │
                   │  Knowledge Base      │
                   │  (IRC, CPHEEO, SWM)  │
                   └────────┬─────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
     ┌────────▼───┐  ┌─────▼─────┐  ┌───▼──────────┐
     │ PostgreSQL │  │ File      │  │ FAISS Index  │
     │ (SQL data) │  │ Storage   │  │ (vectors)    │
     └────────────┘  │(uploads/) │  └──────────────┘
                     └───────────┘
```

## 2. Component Responsibilities

### 2.1 Frontend (`frontend/`)
| Component | Responsibility |
|---|---|
| `Navbar.tsx` | Navigation, auth state display |
| `MapView.tsx` | Leaflet map with colored severity markers |
| `UploadPanel.tsx` | Drag-drop image upload with preview |
| `IssueCard.tsx` | Compact issue display card |
| `Dashboard.tsx` | Stats cards + map + recent reports |
| `ReportIssue.tsx` | Full report submission form with GPS |
| `IssueDetails.tsx` | AI analysis results + before/after images |
| `Analytics.tsx` | Recharts: trends, pie, bar visualizations |
| `Login.tsx` | Auth login/register form |

### 2.2 Backend API (`backend/app/api/`)
| Route | Purpose |
|---|---|
| `POST /api/auth/register` | Create new user account |
| `POST /api/auth/login` | OAuth2 JWT token issuance |
| `GET /api/auth/me` | Get current user profile |
| `POST /api/reports` | Create issue report (multipart w/ images) |
| `GET /api/reports` | List/filter/paginate issues |
| `GET /api/reports/{id}` | Single issue detail |
| `PATCH /api/reports/{id}` | Update status (officer only) |
| `POST /api/reports/{id}/upvote` | Increment upvote count |
| `POST /api/reports/{id}/analyze` | Manually re-trigger AI analysis |
| `GET /api/analytics/dashboard` | Aggregate stats for dashboard |
| `GET /api/analytics/trends` | Monthly time-series data |
| `GET /api/health` | Service health check |

### 2.3 AI Pipeline (`backend/app/services/`)
| Service | Input | Output |
|---|---|---|
| `vision_service` | Image file path | YOLO label + confidence + phash + features |
| `severity_service` | Category + features + text | Severity score 0.0–1.0 |
| `duplicate_service` | Issue metadata + embedding | is_duplicate + duplicate_of_id |
| `location_service` | Category + severity | Evidence-based recommendation text |
| `report_service` | Full Issue object | Orchestrates all above, persists results |

### 2.4 Data Models (SQLAlchemy → PostgreSQL)

**users** → stores citizen/officer/admin accounts  
**issues** → core problem records with AI analysis fields  
**evidence** → image/video/audio attachments with phash + embedding IDs  

## 3. AI Pipeline Flow (per report)

```
REPORT SUBMITTED
       │
       ▼
[1. VISION ANALYSIS]
  ├─ OpenCV load + resize
  ├─ YOLOv8n inference (CPU, ~200ms/image)
  ├─ Perceptual hash (dHash 16x16)
  └─ Feature extraction (edge_density, contrast, etc.)
       │
       ▼
[2. SEVERITY SCORING]
  ├─ XGBoost predict_proba (if model loaded)
  ├─ Fallback: weighted heuristic score
  └─ Map score → LOW/MEDIUM/HIGH/CRITICAL
       │
       ▼
[3. DUPLICATE CHECK]
  ├─ Query recent same-category issues (last 30d)
  ├─ phash Hamming distance ≤ 10 → 45% signal
  ├─ Sentence embedding cosine ≥ 0.82 → 30% signal
  ├─ Haversine distance ≤ 300m → 30% signal
  └─ Combined ≥ 75% → flag as duplicate
       │
       ▼
[4. RECOMMENDATION]
  └─ Lookup from curated IRC/CPHEEO/SWM knowledge base
       │
       ▼
[5. PERSIST + RETURN]
  └─ Write to Issue + Evidence records, return AIAnalysisResult
```

## 4. Security Architecture

```
Client (Browser)
    │  HTTPS (port 443 in prod)
    ▼
Nginx Reverse Proxy (optional)
    │  Bearer JWT in Authorization header
    ▼
FastAPI
    ├─ JWT decoded via python-jose (HS256)
    ├─ sub → user_id, role checked per endpoint
    ├─ bcrypt password hash (cost factor 12)
    ├─ CORS restricted to configured origins
    ├─ File uploads: type + size validated
    └─ Location: optional, privacy-preserving (rounded to 3 decimals)
```

## 5. Technology Decisions

| Choice | Rationale |
|---|---|
| **FastAPI** over Flask | Async I/O, auto-docs (OpenAPI), type safety, 2–3x faster |
| **PostgreSQL** over MongoDB | Structured relational data, GIS queries, JSONB where needed |
| **YOLOv8n (Nano)** over larger models | CPU-only inference, 6.3MB model, good accuracy trade-off |
| **XGBoost** over deep learning | Interpretable, fast, works well on tabular features |
| **FAISS** over Pinecone | Free, local, no external API dependency for MVP |
| **sentence-transformers all-MiniLM-L6-v2** | 384-dim, 80MB, fast CPU inference, good quality |
| **Perceptual hash (dHash)** over feature matching | Fast image dup check, no GPU needed |
| **React + Vite** over Next.js | SPA is fine (no SEO needed), lighter, faster dev |
| **Tailwind CSS** | Utility-first, no CSS file management, fast prototyping |
| **Leaflet** over Mapbox GL | Free, no API key, open data tiles (OSM/CartoDB) |
| **Zustand** over Redux | Minimal boilerplate for simple auth state |
| **Docker Compose** | Reproducible environment, easy deployment |

## 6. Scalability Path (post-MVP)

```
MVP (this system)          → Production Scale
───────────────────────    ─────────────────────────────────
Single PostgreSQL          → PgBouncer + read replicas
CPU YOLOv8n               → ONNX/TensorRT + GPU (T4)
Sync AI pipeline          → Celery + Redis queue
Local file storage        → S3/MinIO/Cloudflare R2
Single FastAPI worker     → Uvicorn Gunicorn workers + K8s
Manual FAISS rebuild      → Vector DB (Qdrant/Weaviate)
No rate limiting          → Nginx rate limit + Redis
Static recommendations    → RAG with municipal document corpus
```
