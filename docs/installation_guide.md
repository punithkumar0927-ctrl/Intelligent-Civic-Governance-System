# NEXUS AI - Installation Guide

## Prerequisites

| Requirement | Version | Check |
|---|---|---|
| Python | 3.10 – 3.12 | `python --version` |
| Node.js | 18 – 22 | `node --version` |
| npm | 9+ | `npm --version` |
| PostgreSQL | 15+ with PostGIS | `psql --version` |
| Git | 2.0+ | `git --version` |

## Quick Start (Docker)

```bash
git clone https://github.com/your-repo/nexus-ai.git
cd nexus-ai
cp .env.example .env
docker-compose up --build
```

Open: http://localhost:5173 (frontend) | http://localhost:8000/docs (API)

## Manual Setup (Windows PowerShell)

### 1. Clone and Setup
```powershell
git clone https://github.com/your-repo/nexus-ai.git
cd nexus-ai
.\scripts\setup_project.ps1
```

### 2. Database Setup
```powershell
# Option A: Use Docker for PostgreSQL
docker run -d --name nexus-db -p 5432:5432 `
  -e POSTGRES_DB=nexus_ai -e POSTGRES_PASSWORD=yourpassword `
  postgis/postgis:15-3.4

# Option B: Local PostgreSQL
createdb nexus_ai
psql -d nexus_ai -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -d nexus_ai -f database/init.sql
```

### 3. Environment Variables
Edit `.env` (see `.env.example`):
```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/nexus_ai
SECRET_KEY=change-this-to-a-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
UPLOAD_DIR=storage/uploads
```

### 4. Seed Demo Data
```powershell
.\venv\Scripts\Activate.ps1
python database/seed_data.py
```

### 5. Install Frontend Dependencies
```powershell
cd frontend
npm install
cd ..
```

### 6. Start Backend
```powershell
.\scripts\run_backend.ps1
```

### 7. Start Frontend (new terminal)
```powershell
cd frontend
npm run dev
```

Open http://localhost:5173 – Login: `citizen1` / `nexus123`

## Model Files

The following model files are needed for full AI functionality:

| File | Location | Download |
|---|---|---|
| YOLOv8n pretrained | `ai_engine/models/detection/yolov8n.pt` | Auto-downloaded by ultralytics |
| Fine-tuned RDD2022 | `ai_engine/models/detection/yolov8n_rdd2022.pt` | Train via notebook 03 |
| XGBoost severity | `ai_engine/models/severity/severity_model.json` | Train via notebook 04 |
| sentence-transformers | Auto-downloads from HuggingFace | First run requires internet |

**Without model files**: The system falls back to heuristic scoring. All features still work but with reduced accuracy.

## Dataset Setup

```powershell
# Create placeholder data for testing the pipeline
python scripts/download_datasets.py placeholder

# Validate data format
python scripts/validate_dataset.py
```

For real training data:
1. Register at https://rdd2022.in
2. Download the train/test archives
3. Place in `datasets/road_damage/raw/`
4. Run `python scripts/convert_annotations.py coco <json> <images> <labels>`

## Troubleshooting

**Backend fails to start**: Check `DATABASE_URL` in `.env` and PostgreSQL running  
**401 on all API calls**: Token expired – re-login  
**No images in uploads**: Run `scripts/setup_project.ps1` to create storage dirs  
**Module not found**: Activate virtual environment first  
**OSM timeout**: Nominatim rate-limited (1 req/sec); system falls back to coordinate-only  
**Model file not found**: Heuristic fallback is used automatically – no error
