# NEXUS AI - Deployment Guide

## Production Architecture

```
Internet
    |
[nginx reverse proxy :443]
    |-- /api/*      -> [FastAPI :8000 (Gunicorn workers)]
    |-- /uploads/*  -> filesystem (static)
    +-- /*          -> [React SPA (static files)]

[FastAPI workers]
    |
[PostgreSQL + PostGIS :5432]

Background tasks:
    - OSM geocoding (async)
    - FAISS index rebuild (nightly)
```

## Docker Compose (Full Stack)

```bash
cp .env.example .env
# Edit .env: set SECRET_KEY, DATABASE_URL, POSTGRES_PASSWORD
docker-compose up -d --build
```

Services exposed:
- `db`: PostgreSQL 15 + PostGIS 3.4
- `backend`: FastAPI via Gunicorn (4 workers)
- `frontend`: nginx serving Vite build

## Nginx Configuration

See `deployment/nginx.conf` for the full reverse proxy config.

Key settings:
```nginx
client_max_body_size 25m;
location /api/ { proxy_pass http://backend:8000/; }
location /uploads/ { alias /app/storage/uploads/; }
location / { root /usr/share/nginx/html; try_files $uri /index.html; }
```

## Gunicorn (Backend)

```bash
cd backend
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

## Environment Variables (Production)

| Variable | Required | Example |
|---|---|---|
| DATABASE_URL | Yes | postgresql://user:pass@db:5432/nexus_ai |
| SECRET_KEY | Yes | Long random string (secrets.token_hex(32)) |
| UPLOAD_DIR | Yes | /app/storage/uploads |
| CORS_ORIGINS | Yes | https://yourdomain.com |

## Model Files

Place trained weights in `ai_engine/models/`:
- detection/yolov8n_rdd2022.pt
- severity/severity_model.json
- embeddings/faiss_index.bin

These files should NOT be in Git. Use a model registry (HuggingFace Hub, DVC, or private S3).

## SSL / HTTPS

```bash
sudo certbot --nginx -d yourdomain.com
```

## Scaling Checklist

- [ ] Redis + Celery for background AI inference
- [ ] FAISS as dedicated microservice
- [ ] PgBouncer connection pooling
- [ ] CDN for uploaded images
- [ ] Horizontal scaling: multiple Gunicorn workers

## Rollback

```bash
docker-compose down
psql -U postgres -d nexus_ai < /backups/nexus_ai_<date>.sql
docker-compose up -d
```
