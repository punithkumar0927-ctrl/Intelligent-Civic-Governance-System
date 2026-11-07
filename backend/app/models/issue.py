from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, Text, ForeignKey, Enum, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class IssueCategory(str, enum.Enum):
    ROAD_DAMAGE    = "road_damage"
    POTHOLE        = "pothole"
    GARBAGE        = "garbage"
    STREETLIGHT    = "streetlight"
    WATER_LEAK     = "water_leak"
    DRAINAGE       = "drainage"
    SIDEWALK       = "sidewalk"
    TRAFFIC_SIGN   = "traffic_sign"
    PARK           = "park"
    BUILDING       = "building"
    POWER_LINE     = "power_line"
    OTHER          = "other"


class IssueStatus(str, enum.Enum):
    PENDING      = "pending"
    UNDER_REVIEW = "under_review"
    IN_PROGRESS  = "in_progress"
    RESOLUTION_SUBMITTED = "resolution_submitted"
    VERIFIED_RESOLVED = "verified_resolved"
    RESOLVED     = "resolved"
    REJECTED     = "rejected"
    DUPLICATE    = "duplicate"


class SeverityLevel(str, enum.Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


class Issue(Base):
    __tablename__ = "issues"

    id              = Column(Integer, primary_key=True, index=True)
    title           = Column(String(200), nullable=False)
    description     = Column(Text, nullable=True)
    category        = Column(Enum(IssueCategory), default=IssueCategory.OTHER, nullable=False)
    status          = Column(Enum(IssueStatus),  default=IssueStatus.PENDING,  nullable=False)
    severity        = Column(Enum(SeverityLevel), default=SeverityLevel.LOW,   nullable=False)
    severity_score  = Column(Float, default=0.0)   # 0.0 – 1.0 from ML model

    # Geo coordinates (coarse — privacy: actual coords optional)
    latitude     = Column(Float, nullable=True)
    longitude    = Column(Float, nullable=True)
    ward         = Column(String(100), nullable=True)
    city         = Column(String(100), nullable=True)
    state        = Column(String(100), nullable=True)
    address_raw  = Column(String(300), nullable=True)   # user-typed address

    # AI Analysis
    ai_detected_label    = Column(String(100), nullable=True)
    ai_confidence        = Column(Float, nullable=True)
    ai_status            = Column(String(40), nullable=True)  # completed | MODEL_NOT_CONFIGURED | error
    ai_duplicate_of_id   = Column(Integer, ForeignKey("issues.id"), nullable=True)
    is_duplicate         = Column(Boolean, default=False)
    analysis_complete    = Column(Boolean, default=False)

    # Tracking
    reporter_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to   = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution_note  = Column(Text, nullable=True)
    resolved_at        = Column(DateTime(timezone=True), nullable=True)
    upvotes            = Column(Integer, default=0)
    view_count         = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    reporter   = relationship("User", foreign_keys=[reporter_id], back_populates="issues")
    evidence   = relationship("Evidence", back_populates="issue", cascade="all, delete-orphan", lazy="select")
    location   = relationship("Location", back_populates="issue", uselist=False, cascade="all, delete-orphan")
    resolutions = relationship("Resolution", back_populates="issue", cascade="all, delete-orphan")
    duplicates = relationship("Issue", remote_side=[id], foreign_keys=[ai_duplicate_of_id])

    __table_args__ = (
        Index("ix_issues_status",       "status"),
        Index("ix_issues_category",     "category"),
        Index("ix_issues_severity",     "severity"),
        Index("ix_issues_location",     "latitude", "longitude"),
        Index("ix_issues_created",      "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Issue id={self.id} title={self.title!r} status={self.status}>"
