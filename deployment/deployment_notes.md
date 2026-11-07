# NEXUS AI - Deployment Notes

## Target: Single VM – 4 vCPU, 8 GB RAM, 80 GB SSD, Ubuntu 22.04

## Pre-deployment Checklist
- [ ] SECRET_KEY rotated (use: `python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] POSTGRES_PASSWORD set (not default)
- [ ] Database migrated or seeded
- [ ] Model files copied to ai_engine/models/
- [ ] CORS_ORIGINS set to actual domain
- [ ] SSL certificate valid
- [ ] /api/health responding 200

## Known Operational Issues

| Issue | Mitigation |
|---|---|
| Nominatim 429 rate limit | Cache geocode results in locations table |
| Large upload timeout | Nginx client_max_body_size = 25m; Gunicorn timeout = 120s |
| YOLOv8 CPU inference slow | Use imgsz=320 for preview; full 640 for final |
| FAISS memory | Keep in worker RAM; rebuild nightly from DB |
| Connection pool exhausted | SQLAlchemy pool_size=20, max_overflow=40 |

## Backup

```bash
# Daily PostgreSQL dump
pg_dump -U postgres nexus_ai > /backups/nexus_$(date +%Y%m%d).sql

# Weekly uploads backup
rsync -avz storage/uploads/ backup-server:/nexus-uploads/
```

## Performance Reference
- Full report pipeline: ~1.2s per image (CPU, single worker)
- Concurrent requests supported: 4 (Gunicorn workers)
- YOLOv8n inference: ~200ms/image on 4-core CPU
- XGBoost severity: ~2ms
- FAISS search (10k vectors): ~5ms
- Nominatim geocode (cached): ~0ms
