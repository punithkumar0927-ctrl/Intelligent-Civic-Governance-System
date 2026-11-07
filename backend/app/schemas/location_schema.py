"""schemas/location_schema.py — Pydantic models for Location and Geo analytics."""
from typing import Optional
from pydantic import BaseModel, Field


class LocationInput(BaseModel):
    latitude:    Optional[float] = Field(None, ge=-90, le=90)
    longitude:   Optional[float] = Field(None, ge=-180, le=180)
    ward:        Optional[str]   = Field(None, max_length=100)
    zone:        Optional[str]   = Field(None, max_length=100)
    city:        Optional[str]   = Field(None, max_length=100)
    state:       Optional[str]   = Field(None, max_length=100)
    pincode:     Optional[str]   = Field(None, pattern=r"^[1-9]\d{5}$")
    address_raw: Optional[str]   = Field(None, max_length=300)
    landmark_type: Optional[str] = None
    landmark_name: Optional[str] = None


class LocationOut(BaseModel):
    id:               int
    issue_id:         int
    latitude:         Optional[float]
    longitude:        Optional[float]
    ward:             Optional[str]
    zone:             Optional[str]
    city:             Optional[str]
    state:            Optional[str]
    pincode:          Optional[str]
    osm_road_name:    Optional[str]
    osm_place_name:   Optional[str]
    landmark_type:    Optional[str]
    landmark_name:    Optional[str]
    landmark_dist_m:  Optional[float]
    risk_score:       float
    is_high_risk_zone: bool
    geocoded:         bool

    class Config:
        from_attributes = True


class GeoPoint(BaseModel):
    id:       int
    lat:      float
    lon:      float
    severity: str
    category: str
    status:   str
    ward:     Optional[str] = None


class HotspotCluster(BaseModel):
    ward:           str
    count:          int
    avg_severity:   float
    top_category:   str
    lat:            float
    lon:            float


class WardReport(BaseModel):
    ward:              str
    city:              Optional[str]
    total_issues:      int
    resolved:          int
    resolution_rate:   float
    critical_count:    int
    avg_resolution_days: float


class GeoAnalyticsResponse(BaseModel):
    total_points:      int
    clusters:          list[HotspotCluster]
    ward_reports:      list[WardReport]
    high_risk_count:   int
