from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Location(Base):
    """
    Normalized location entity linked to Issues.
    Separates raw address text from geocoded data and ward metadata.
    """
    __tablename__ = "locations"

    id          = Column(Integer, primary_key=True, index=True)
    issue_id    = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Raw user input
    address_raw = Column(String(300), nullable=True)

    # Precise coordinates (privacy: rounded to 3 decimals before public display)
    latitude    = Column(Float, nullable=True)
    longitude   = Column(Float, nullable=True)

    # Admin geography
    ward        = Column(String(100),  nullable=True)
    zone        = Column(String(100),  nullable=True)
    city        = Column(String(100),  nullable=True)
    state       = Column(String(100),  nullable=True)
    country     = Column(String(50),   default="India")
    pincode     = Column(String(10),   nullable=True)

    # OSM / reverse-geocoding results
    osm_road_name    = Column(String(200), nullable=True)
    osm_place_name   = Column(String(200), nullable=True)
    osm_nearest_km   = Column(Float, nullable=True)

    # Nearest landmark (school, hospital, junction, etc.)
    landmark_type    = Column(String(80),  nullable=True)  # school | hospital | junction | market
    landmark_name    = Column(String(200), nullable=True)
    landmark_dist_m  = Column(Float, nullable=True)        # metres to landmark

    # Risk overlay: how sensitive is this location?
    risk_score       = Column(Float, default=0.0)          # 0.0–1.0
    is_high_risk_zone = Column(Boolean, default=False)     # school/hospital zone flag

    # Processing state
    geocoded        = Column(Boolean, default=False)
    geocode_source  = Column(String(30), nullable=True)    # nominatim | photon | manual
    processed_at    = Column(DateTime(timezone=True), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    issue = relationship("Issue", back_populates="location")

    __table_args__ = (
        Index("ix_locations_lat_lon",   "latitude", "longitude"),
        Index("ix_locations_ward",      "ward"),
        Index("ix_locations_city",      "city"),
        Index("ix_locations_risk",      "is_high_risk_zone"),
    )

    def __repr__(self) -> str:
        return f"<Location id={self.id} ward={self.ward!r} lat={self.latitude}>"
