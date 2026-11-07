from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base


class SavedPlace(Base):
    """A location a signed-in user chose on Google Maps. Not a public dataset."""

    __tablename__ = "saved_places"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    address = Column(String(400), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    category = Column(String(40), nullable=False, default="saved")
    google_place_id = Column(String(160), nullable=True)
    source = Column(String(40), nullable=False, default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_saved_places_user_created", "user_id", "created_at"),
    )
