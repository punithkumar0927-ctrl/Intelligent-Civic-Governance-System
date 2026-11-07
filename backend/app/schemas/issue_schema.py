"""schemas/issue_schema.py — Pydantic models for Issue entities."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.issue import IssueCategory, IssueStatus, SeverityLevel


class IssueCreate(BaseModel):
    title:        str              = Field(..., min_length=5, max_length=200)
    description:  Optional[str]    = Field(None, max_length=2000)
    category:     IssueCategory    = IssueCategory.OTHER
    latitude:     Optional[float]  = Field(None, ge=-90, le=90)
    longitude:    Optional[float]  = Field(None, ge=-180, le=180)
    ward:         Optional[str]    = Field(None, max_length=100)
    city:         Optional[str]    = Field(None, max_length=100)
    state:        Optional[str]    = Field(None, max_length=100)
    address_raw:  Optional[str]    = Field(None, max_length=300)
    pincode:      Optional[str]    = Field(None, pattern=r"^[1-9]\d{5}$")
    landmark_type: Optional[str]   = Field(None, max_length=80)


class IssueUpdate(BaseModel):
    title:           Optional[str]         = None
    description:     Optional[str]         = None
    status:          Optional[IssueStatus] = None
    severity:        Optional[SeverityLevel] = None
    ward:            Optional[str]         = None
    city:            Optional[str]         = None
    resolution_note: Optional[str]         = None
    assigned_to:     Optional[int]         = None


class IssueOut(BaseModel):
    id:                int
    title:             str
    description:       Optional[str]
    category:          IssueCategory
    status:            IssueStatus
    severity:          SeverityLevel
    severity_score:    float
    latitude:          Optional[float]
    longitude:         Optional[float]
    ward:              Optional[str]
    city:              Optional[str]
    ai_detected_label: Optional[str]
    ai_confidence:     Optional[float]
    is_duplicate:      bool
    upvotes:           int
    view_count:        int
    reporter:          "UserOut"
    created_at:        datetime
    updated_at:        Optional[datetime]

    class Config:
        from_attributes = True


class IssueListOut(BaseModel):
    items:    list[IssueOut]
    total:    int
    page:     int
    per_page: int


class AIAnalysisResult(BaseModel):
    issue_id:           int
    detected_label:     Optional[str]
    confidence:         Optional[float]
    severity_score:     float
    severity_level:     SeverityLevel
    duplicate_detected: bool
    duplicate_of_id:    Optional[int]
    recommendation:     Optional[str]
    analysis_complete:  bool


# Forward ref fix
from app.schemas.user_schema import UserOut
IssueOut.model_rebuild()
