"""schemas/verification_schema.py — Pydantic models for repair verification."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.resolution import VerificationStatus


class VerificationCreate(BaseModel):
    issue_id:    int
    after_image_note: Optional[str] = Field(None, max_length=500)


class VerificationUpdate(BaseModel):
    verification_status: Optional[VerificationStatus] = None
    officer_note:        Optional[str] = None
    human_verified:      Optional[bool] = None


class VerificationResult(BaseModel):
    """AI comparison result returned to frontend."""
    resolution_id:         int
    issue_id:              int
    ssim_score:            Optional[float]
    edge_density_before:   Optional[float]
    edge_density_after:    Optional[float]
    edge_reduction:        Optional[float]
    brightness_delta:      Optional[float]
    resolved_probability:  Optional[float]
    ai_recommendation:     Optional[str]
    verification_status:   VerificationStatus
    human_verified:        bool
    officer_note:          Optional[str]
    verified_at:           Optional[datetime]
    created_at:            datetime


class VerificationSummary(BaseModel):
    total_pending:     int
    total_verified:    int
    total_rejected:    int
    avg_confidence:    float
    verification_rate: float


class BeforeAfterPair(BaseModel):
    resolution_id:        int
    issue_id:             int
    title:                str
    category:             str
    severity:             str
    before_image_url:     Optional[str]
    after_image_url:      Optional[str]
    resolved_probability: Optional[float]
    ssim_score:           Optional[float]
    ai_recommendation:    Optional[str]
    verification_status:  str
