"""
ai_engine/geographic_intelligence/gps_processor.py
GPS data extraction, cleaning, and privacy handling.
"""
import math
from typing import Optional
from dataclasses import dataclass


@dataclass
class GCSCoordinate:
    lat: float
    lon: float
    alt: Optional[float] = None
    accuracy_m: Optional[float] = None
    source: str = "unknown"  # exif | browser | manual | osm

    def is_valid(self) -> bool:
        return -90 <= self.lat <= 90 and -180 <= self.lon <= 180

    def anonymized(self, precision: int = 3) -> "GCSCoordinate":
        return GCSCoordinate(
            lat=round(self.lat, precision),
            lon=round(self.lon, precision),
            alt=self.alt,
            source=self.source,
        )

    def to_dms(self) -> tuple:
        def _deg_to_dms(deg: float) -> tuple:
            d = int(abs(deg))
            m = int((abs(deg) - d) * 60)
            s = round((abs(deg) - d - m / 60) * 3600, 2)
            return d, m, s
        lat_dms = _deg_to_dms(self.lat)
        lon_dms = _deg_to_dms(self.lon)
        lat_dir = "N" if self.lat >= 0 else "S"
        lon_dir = "E" if self.lon >= 0 else "W"
        return (lat_dms[0], lat_dms[1], lat_dms[2], lat_dir,
                lon_dms[0], lon_dms[1], lon_dms[2], lon_dir)

    def distance_to(self, other: "GCSCoordinate") -> float:
        """Haversine distance in kilometres."""
        R = 6371.0
        dlat = math.radians(other.lat - self.lat)
        dlon = math.radians(other.lon - self.lon)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(self.lat)) * math.cos(math.radians(other.lat)) *
             math.sin(dlon / 2) ** 2)
        return R * 2 * math.asin(math.sqrt(a))


def extract_gps_from_exif(image_path: str) -> Optional[GCSCoordinate]:
    try:
        from PIL import Image
        from PIL.ExifTags import GPSTAGS
        img = Image.open(image_path)
        exif = img._getexif()
        if not exif:
            return None
        gps_raw = exif.get(34853)
        if not gps_raw:
            return None
        gps = {GPSTAGS.get(k, k): v for k, v in gps_raw.items()}
        if "GPSLatitude" not in gps:
            return None

        def dms_to_deg(dms, ref):
            d = float(dms[0]); m = float(dms[1]); s = float(dms[2])
            deg = d + m / 60.0 + s / 3600.0
            return -deg if ref in ("S", "W") else deg

        lat = dms_to_deg(gps["GPSLatitude"], gps.get("GPSLatitudeRef", "N"))
        lon = dms_to_deg(gps["GPSLongitude"], gps.get("GPSLongitudeRef", "E"))
        return GCSCoordinate(lat=lat, lon=lon, source="exif")
    except Exception as exc:
        print(f"[gps_processor] EXIF GPS error: {exc}")
        return None


def is_within_bbox(lat: float, lon: float,
                   bbox: tuple[float, float, float, float]) -> bool:
    """Check if point is within (min_lat, min_lon, max_lat, max_lon)."""
    return bbox[0] <= lat <= bbox[2] and bbox[1] <= lon <= bbox[3]


# India bounding box for validation
INDIA_BBOX = (6.0, 68.0, 37.0, 98.0)


def is_in_india(coord: GCSCoordinate) -> bool:
    return is_within_bbox(coord.lat, coord.lon, INDIA_BBOX)
