from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health")
def health_check():
    return {
        "status":    "healthy",
        "service":   "NEXUS AI Backend",
        "version":   "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready")
def readiness():
    """Kubernetes / load-balancer readiness probe."""
    return {"ready": True}
