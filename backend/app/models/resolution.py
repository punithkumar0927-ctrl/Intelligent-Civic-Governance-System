from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class VerificationStatus(str, enum.Enum):
    PENDING     = "pending"       # awaiting after-photo
    ANALYZING   = "analyzing"     # AI pipeline running
    LIKELY_FIXED = "likely_fixed"
    PARTIALLY_FIXED = "partially_fixed"
    NOT_FIXED   = "not_fixed"
    NEEDS_REVIEW = "needs_review"  # human review required
    CONFIRMED_FIXED = "confirmed_fixed"
    REJECTED    = "rejected"       # false resolution claim


class Resolution(Base):
    """
    Tracks repair verification for an Issue.
    Created when officer marks an issue as 'resolved' or when
    a citizen uploads an after-photo for community verification.
    """
    __tablename__ = "resolutions"

    id              = Column(Integer, primary_key=True, index=True)
    issue_id        = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    verifier_id     = Column(Integer, ForeignKey("users.id"), nullable=True)   # officer who marked resolved

    # Before/After image IDs (evidence FK)
    before_evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=True)
    after_evidence_id  = Column(Integer, ForeignKey("evidence.id"), nullable=True)

    # AI comparison results
    ssim_score           = Column(Float, nullable=True)   # structural similarity 0–1
    edge_reduction       = Column(Float, nullable=True)   # % reduction in edge density
    brightness_delta     = Column(Float, nullable=True)
    resolved_probability = Column(Float, nullable=True)   # composite 0–1 score

    # Officer / human review
    verification_status  = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    officer_note         = Column(Text, nullable=True)
    human_verified       = Column(Boolean, default=False)
    verified_at          = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    resolution_claimed_at = Column(DateTime(timezone=True), nullable=True)
    created_at            = Column(DateTime(timezone=True), server_default=func.now())
    updated_at            = Column(DateTime(timezone=True), onupdate=func.now())

    issue    = relationship("Issue", back_populates="resolutions")
    verifier = relationship("User",   foreign_keys=[verifier_id])

    def __repr__(self) -> str:
        return f"<Resolution id={self.id} issue_id={self.issue_id} status={self.verification_status}>"
