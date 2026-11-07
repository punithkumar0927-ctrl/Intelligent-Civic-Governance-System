from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.issue import IssueCategory, IssueStatus, SeverityLevel


# ── Auth ─────────────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    username:   str        = Field(..., min_length=3, max_length=50)
    email:      EmailStr
    full_name:  Optional[str] = Field(None, max_length=100)
    phone:      Optional[str] = Field(None, max_length=15)
    password:   str        = Field(..., min_length=8)


class UserLogin(BaseModel):
    email:    EmailStr
    password: str


class UserOut(BaseModel):
    id:         int
    username:   str
    email:      str
    full_name:  Optional[str]
    phone:      Optional[str] = None
    role:       str
    is_verified: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=15)


class PasswordChange(BaseModel):
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)


class EmailToken(BaseModel):
    token: str = Field(..., min_length=10)


class ForgotPassword(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    token: str = Field(..., min_length=10)
    password: str = Field(..., min_length=8)


class RefreshRequest(BaseModel):
    refresh_token: str


class Message(BaseModel):
    detail: str
    dev_token: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    refresh_token: Optional[str] = None
    user:         UserOut
    dev_verification_token: Optional[str] = None
    message: Optional[str] = None


# ── Issue ────────────────────────────────────────────────────────────────────
class IssueCreate(BaseModel):
    title:        str           = Field(..., min_length=5, max_length=200)
    description:  Optional[str] = Field(None, max_length=2000)
    category:     IssueCategory = IssueCategory.OTHER
    latitude:     Optional[float] = Field(None, ge=-90, le=90)
    longitude:    Optional[float] = Field(None, ge=-180, le=180)
    ward:         Optional[str] = Field(None, max_length=100)
    city:         Optional[str] = Field(None, max_length=100)
    state:        Optional[str] = Field(None, max_length=100)
    address_raw:  Optional[str] = Field(None, max_length=300)


class IssueUpdate(BaseModel):
    title:        Optional[str] = None
    description:  Optional[str] = None
    status:       Optional[IssueStatus] = None
    severity:     Optional[SeverityLevel] = None
    ward:         Optional[str] = None
    city:         Optional[str] = None
    resolution_note: Optional[str] = None


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
    reporter:          UserOut
    created_at:        datetime
    updated_at:        Optional[datetime]

    class Config:
        from_attributes = True


class IssueListOut(BaseModel):
    items:    list[IssueOut]
    total:    int
    page:     int
    per_page: int


# ── Evidence ─────────────────────────────────────────────────────────────────
class EvidenceOut(BaseModel):
    id:              int
    issue_id:        int
    evidence_type:   str
    file_name:       str
    file_url:        Optional[str]
    yolo_label:      Optional[str]
    yolo_confidence: Optional[float]
    verified:        bool
    created_at:      datetime

    class Config:
        from_attributes = True


# ── Analytics ────────────────────────────────────────────────────────────────
class CategoryCount(BaseModel):
    category: str
    count:    int


class StatusCount(BaseModel):
    status: str
    count:  int


class SeverityCount(BaseModel):
    severity: str
    count:    int


class GeoPoint(BaseModel):
    id:        int
    lat:       float
    lon:       float
    severity:  str
    category:  str
    status:    str


class DashboardStats(BaseModel):
    total_issues:          int
    active_issues:         int
    high_severity_issues:  int
    resolved_issues:       int
    verified_resolutions:  int
    duplicate_reports:     int
    ai_detection_accuracy: Optional[float]
    demo_data:             bool
    pending_issues:        int
    critical_issues:       int
    avg_resolution_days:   float
    resolution_rate:       float
    by_category:           list[CategoryCount]
    by_status:             list[StatusCount]
    by_severity:           list[SeverityCount]
    geo_points:            list[GeoPoint]


# ── AI Analysis Response ─────────────────────────────────────────────────────
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
    detection_status:   Optional[str] = None
    model_note:         Optional[str] = None
