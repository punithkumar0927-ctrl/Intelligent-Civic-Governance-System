from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class GpsPhoto(Base):
    """A photograph uploaded by one user. Files stay outside the public upload folder."""

    __tablename__ = "gps_photos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_name = Column(String(255), nullable=False)
    watermark_stored_name = Column(String(255), nullable=True)
    mime_type = Column(String(80), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    gps_accuracy = Column(Float, nullable=True)
    location_address = Column(String(400), nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    watermark_enabled = Column(Boolean, nullable=False, default=False)
