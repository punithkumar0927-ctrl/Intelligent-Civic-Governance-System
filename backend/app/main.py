"""
NEXUS AI — FastAPI Application Entry Point
The Living Intelligence Map for Urban Infrastructure
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.database import init_db
from app.api import admin, ai_reports, auth, civic, demo_video, detection, gps_photos, maps, places, reports, analytics, health, geographic, verification


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables (dev only — use Alembic in production)
    if settings.ENVIRONMENT == "development":
        init_db()
        print("[NEXUS AI] Database initialized")
    # Ensure upload dir exists
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    print(f"[NEXUS AI] Server ready on http://{settings.HOST}:{settings.PORT}")
    yield
    print("[NEXUS AI] Shutdown")


app = FastAPI(
    title="NEXUS AI — The Living Intelligence Map",
    description=(
        "Intelligent urban infrastructure monitoring using Computer Vision, "
        "Multimodal AI, Severity Prediction, and Geospatial Analytics."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files (uploaded images) ───────────────────────────────────────────
upload_path = Path(settings.UPLOAD_DIR)
upload_path.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

# ── API Routers ──────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(analytics.router)
app.include_router(geographic.router)
app.include_router(verification.router)
app.include_router(admin.router)
app.include_router(detection.router)
app.include_router(ai_reports.router)
app.include_router(places.router)
app.include_router(maps.router)
app.include_router(gps_photos.router)
app.include_router(demo_video.router)
app.include_router(civic.router)


# ── Root ─────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
def root():
    return {
        "service":   "NEXUS AI",
        "tagline":   "The Living Intelligence Map",
        "docs":      "/api/docs",
        "health":    "/api/health",
        "version":   "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
    )
