# NEXUS AI - Database Design

## Engine: PostgreSQL 15 + PostGIS 3.4

## Entity-Relationship Diagram (text)

```
users (1) ──── (N) issues (1) ──── (1) locations
                    |
                   (N)
                    |
               evidences (N) ──── (1) resolutions
                    |
               duplicate_links
                    |
              hotspot_cache
```

## Table Definitions

### users
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| username | VARCHAR(64) UNIQUE | Login identifier |
| email | VARCHAR(255) UNIQUE | |
| hashed_password | VARCHAR(255) | bcrypt; never plaintext |
| full_name | VARCHAR(255) | |
| phone | VARCHAR(20) | Optional; for officer contact |
| role | VARCHAR(20) | citizen / officer / admin |
| city, ward | VARCHAR(100) | Default work area |
| is_active | BOOLEAN | Soft-deactivate without delete |
| created_at | TIMESTAMPTZ | |

### issues
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| title | VARCHAR(300) | |
| description | TEXT | |
| category | VARCHAR(50) | pothole/road_damage/garbage/drainage/... |
| severity | VARCHAR(20) | low/medium/high/critical |
| status | VARCHAR(30) | open/in_progress/resolved/rejected/duplicate |
| latitude | DECIMAL(10,7) | WGS84 |
| longitude | DECIMAL(10,7) | WGS84 |
| location | GEOGRAPHY(Point,4326) | Auto-updated by trigger |
| ward, city, pincode | VARCHAR | Administrative |
| reporter_id | FK → users | |
| duplicate_of | FK → issues | Points to primary issue |
| duplicate_count | INTEGER | Aggregated from links |
| ai_detected_label | VARCHAR(100) | YOLO class name |
| ai_confidence | DECIMAL(5,4) | YOLO confidence score |
| created_at, updated_at, resolved_at | TIMESTAMPTZ | |

Indexes: GiST(location), BTREE(status, severity, category, city, ward, created_at DESC)

### locations
1:1 with issues; stores OSM-enriched fields.

| Key Fields | Notes |
|---|---|
| osm_road_name | From Nominatim reverse geocode |
| landmark_type/name | Nearest amenity (school, hospital, etc.) |
| risk_score | 0-1 composite from proximity to sensitive sites |
| is_high_risk_zone | Boolean; true if near school/hospital within 400m |
| geocoded | Whether OSM lookup succeeded |
| geocode_source | "nominatim" or "offline_pbf" |

### evidences
| Key Fields | Notes |
|---|---|
| evidence_type | IMAGE_BEFORE / IMAGE_AFTER / IMAGE_OTHER / DOCUMENT |
| file_path | Absolute path on server storage |
| thumbnail_path | 300px version for list view |
| uploader_id | FK to users who uploaded |

### resolutions
One per issue; updated when after-photo is uploaded.

| Key Fields | Notes |
|---|---|
| ssim_score | SSIM similarity 0-1 |
| edge_reduction | Fraction of edge density removed (positive = repair) |
| resolved_probability | Composite AI confidence 0-1 |
| verification_status | pending / analyzing / likely_fixed / partially_fixed / needs_review / not_fixed / confirmed_fixed / rejected |
| human_verified | Officer confirmed or rejected the AI verdict |

### duplicate_links
Stores pairwise similarity scores between issues.

### hotspot_cache
Cached output of `find_hotspot_clusters()` for dashboard queries without re-running DBSCAN.

## PostGIS Queries

### Nearby issues (radius search)
```sql
SELECT i.*
FROM issues i
WHERE ST_DWithin(i.location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius_m)
  AND i.status != 'duplicate'
ORDER BY i.created_at DESC;
```

### Hotspot centroid assignment
```sql
SELECT ward, COUNT(*) as cnt,
       AVG(CASE severity WHEN 'critical' THEN 4 ... END) as avg_sev
FROM issues
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY ward
ORDER BY avg_sev * COUNT(*) DESC;
```

## Migrations
Use Alembic: `cd backend && alembic revision --autogenerate -m "add_xxx" && alembic upgrade head`
