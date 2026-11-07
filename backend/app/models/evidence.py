from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class EvidenceType(str, enum.Enum):
    IMAGE_BEFORE    = "image_before"
    IMAGE_AFTER     = "image_after"
    VIDEO           = "video"
    AUDIO           = "audio"
    DOCUMENT        = "document"


class Evidence(Base):
    __tablename__ = "evidence"

    id              = Column(Integer, primary_key=True, index=True)
    issue_id        = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    uploader_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    evidence_type   = Column(Enum(EvidenceType), nullable=False)

    # File storage
    file_name       = Column(String(256), nullable=False)
    file_path       = Column(String(512), nullable=False)   # relative path on disk
    file_url        = Column(String(512), nullable=True)    # public URL if S3/CDN
    file_size_bytes = Column(Integer, nullable=True)
    mime_type       = Column(String(80), nullable=True)

    # AI processing results
    phash           = Column(String(64), nullable=True)     # perceptual hash for dup detection
    embedding_id    = Column(String(64), nullable=True)     # FAISS vector ID
    yolo_label      = Column(String(80), nullable=True)
    yolo_confidence = Column(Float, nullable=True)
    img_width       = Column(Integer, nullable=True)
    img_height      = Column(Integer, nullable=True)
    exif_lat        = Column(Float, nullable=True)          # GPS from EXIF (optional)
    exif_lon        = Column(Float, nullable=True)
    ai_analysis     = Column(Text, nullable=True)           # JSON blob of full analysis

    is_public       = Column(Boolean, default=True)         # privacy flag
    verified        = Column(Boolean, default=False)        # human-reviewed
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    issue = relationship("Issue", back_populates="evidence")

    def __repr__(self) -> str:
        return f"<Evidence id={self.id} type={self.evidence_type} issue_id={self.issue_id}>"
