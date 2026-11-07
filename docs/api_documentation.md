# NEXUS AI — API Documentation

> Interactive docs available at `http://localhost:8000/api/docs` (Swagger UI)  
> and `http://localhost:8000/api/redoc` (ReDoc) when the server is running.

---

## Base URL

```
Development:  http://localhost:8000
Production:   https://api.yourdomain.com
```

---

## Authentication

All protected endpoints require a **Bearer JWT token** in the `Authorization` header.

```
Authorization: Bearer <access_token>
```

Obtain token via `/api/auth/login`. Token expires after 60 minutes (configurable).

---

## Endpoints

### 1. Health

#### `GET /api/health`
No auth. Returns service status.

```json
{
  "status": "healthy",
  "service": "NEXUS AI Backend",
  "version": "1.0.0",
  "timestamp": "2025-11-06T10:30:00Z"
}
```

---

### 2. Authentication

#### `POST /api/auth/register`
Create a new citizen account. **No auth required.**

**Request Body** (`application/json`):
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepass123",
  "full_name": "John Doe",
  "phone": "+919876543210"
}
```

**Response** `201 Created`:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "citizen",
    "created_at": "2025-11-06T10:30:00Z"
  }
}
```

**Errors**:
- `400` — Email or username already exists
- `422` — Validation error (password too short, invalid email)

---

#### `POST /api/auth/login`
OAuth2 password flow. Use **email** in the `username` form field.

**Form Fields**:
```
username=john@example.com
password=securepass123
```

**Response** `200 OK`: Same structure as register.

**Errors**:
- `401` — Invalid credentials
- `403` — Account deactivated

---

#### `GET /api/auth/me`
**Auth required.** Returns current user profile.

```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "citizen",
  "created_at": "2025-11-06T10:30:00Z"
}
```

---

### 3. Reports (Issues)

#### `POST /api/reports`
**Auth required.** Create a new issue report. Supports multipart image upload.

**Content-Type**: `multipart/form-data`

**Form Fields**:
| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | Yes | Issue summary (5–200 chars) |
| `description` | string | No | Detailed description (max 2000) |
| `category` | enum | Yes | One of: road_damage, pothole, garbage, streetlight, water_leak, drainage, sidewalk, traffic_sign, park, building, power_line, other |
| `latitude` | float | No | GPS lat (-90 to 90) |
| `longitude` | float | No | GPS lon (-180 to 180) |
| `ward` | string | No | Municipal ward name |
| `city` | string | No | City name |
| `state` | string | No | State name |
| `address_raw` | string | No | Free-text street address |
| `image_before` | file | No | Current state photo (jpeg/png/webp, max 20MB) |
| `image_after` | file | No | After-repair photo |

**Response** `201 Created`:
```json
{
  "id": 42,
  "title": "Large pothole near school gate",
  "description": "Dangerous pothole ~60cm wide forming near Main Road school crossing",
  "category": "pothole",
  "status": "pending",
  "severity": "high",
  "severity_score": 0.6342,
  "latitude": 12.9716,
  "longitude": 77.5946,
  "city": "Bengaluru",
  "ai_detected_label": "pothole",
  "ai_confidence": 0.873,
  "is_duplicate": false,
  "upvotes": 0,
  "view_count": 0,
  "reporter": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "citizen",
    "created_at": "2025-11-01T08:00:00Z"
  },
  "created_at": "2025-11-06T10:30:00Z",
  "updated_at": null
}
```

**AI Pipeline runs automatically** on creation. Response includes analysis results.

---

#### `GET /api/reports`
**Auth required.** List issues with filtering and pagination.

**Query Parameters**:
| Param | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number (min 1) |
| `per_page` | int | 20 | Results per page (1–100) |
| `status` | enum | — | Filter by status |
| `category` | enum | — | Filter by category |
| `severity` | enum | — | Filter by severity |
| `city` | string | — | Partial city name match |
| `q` | string | — | Search in title + description |

**Response** `200 OK`:
```json
{
  "items": [...],
  "total": 127,
  "page": 1,
  "per_page": 20
}
```

---

#### `GET /api/reports/{id}`
**Auth required.** Get single issue detail. Increments view count.

---

#### `PATCH /api/reports/{id}`
**Officer/Admin auth required.** Update issue status, severity, or resolution note.

**Request Body** (JSON, all fields optional):
```json
{
  "status": "resolved",
  "resolution_note": "Pothole filled and compacted by PWD team, 2025-11-06",
  "severity": "medium"
}
```

---

#### `POST /api/reports/{id}/upvote`
**Auth required.** Increment community upvote count.

---

#### `GET /api/reports/{id}/evidence`
**Auth required.** List all evidence files attached to an issue.

---

#### `POST /api/reports/{id}/analyze`
**Auth required.** Manually re-trigger the full AI analysis pipeline for an issue.

**Response** `200 OK`:
```json
{
  "issue_id": 42,
  "detected_label": "pothole",
  "confidence": 0.873,
  "severity_score": 0.6812,
  "severity_level": "high",
  "duplicate_detected": false,
  "duplicate_of_id": null,
  "recommendation": "Priority repair required within 7 days. Hot-mix asphalt patch...",
  "analysis_complete": true
}
```

---

### 4. Analytics

#### `GET /api/analytics/dashboard`
**Auth required.** Returns all dashboard summary statistics.

**Query Param**: `city` (optional string filter)

**Response** `200 OK`:
```json
{
  "total_issues": 127,
  "resolved_issues": 48,
  "pending_issues": 63,
  "critical_issues": 9,
  "avg_resolution_days": 12.4,
  "resolution_rate": 37.8,
  "by_category": [
    {"category": "pothole", "count": 52},
    {"category": "garbage", "count": 31}
  ],
  "by_status": [
    {"status": "pending", "count": 45},
    {"status": "resolved", "count": 48}
  ],
  "by_severity": [
    {"severity": "low", "count": 22},
    {"severity": "medium", "count": 44},
    {"severity": "high", "count": 47},
    {"severity": "critical", "count": 14}
  ],
  "geo_points": [
    {"id": 1, "lat": 12.9716, "lon": 77.5946, "severity": "high", "category": "pothole", "status": "pending"}
  ]
}
```

---

#### `GET /api/analytics/trends`
**Auth required.** Monthly time-series data.

**Query Param**: `months` (int 1–24, default 12)

**Response**:
```json
[
  {"month": "2025-01", "total": 8, "resolved": 3},
  {"month": "2025-02", "total": 14, "resolved": 7}
]
```

---

## Error Format

All errors use standard FastAPI `HTTPException` format:

```json
{
  "detail": "Email already registered"
}
```

**Status codes used**:
| Code | Meaning |
|---|---|
| `400` | Validation error (duplicate username/email) |
| `401` | Missing or invalid JWT token |
| `403` | Insufficient role (officer required) |
| `404` | Resource not found |
| `413` | File too large (>20MB) |
| `422` | Pydantic validation error |

---

## Rate Limiting

Not yet implemented in MVP. Add via:
- Nginx `limit_req_zone` in production
- `slowapi` library in FastAPI for per-user limits

---

## File URLs

Uploaded images served at: `GET /uploads/{filename}`

Static mount in `main.py`. For production, replace with S3/MinIO presigned URLs.
