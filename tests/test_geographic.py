"""tests/test_geographic.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import math
import pytest
from datetime import datetime, timezone


class TestHaversine:
    def test_same_point_zero(self):
        from ai_engine.geographic_intelligence.distance_calculator import haversine_km
        assert haversine_km(12.97, 77.59, 12.97, 77.59) == pytest.approx(0.0, abs=0.01)

    def test_bengaluru_chennai(self):
        from ai_engine.geographic_intelligence.distance_calculator import haversine_km
        # BLR (12.97, 77.59) to MAA (13.08, 80.27) ~290km
        d = haversine_km(12.97, 77.59, 13.08, 80.27)
        assert 250 < d < 350

    def test_symmetry(self):
        from ai_engine.geographic_intelligence.distance_calculator import haversine_km
        d1 = haversine_km(12.9, 77.5, 13.1, 77.7)
        d2 = haversine_km(13.1, 77.7, 12.9, 77.5)
        assert d1 == pytest.approx(d2, abs=0.01)


class TestGCSCoordinate:
    def test_valid(self):
        from ai_engine.geographic_intelligence.gps_processor import GCSCoordinate
        c = GCSCoordinate(lat=12.9716, lon=77.5946)
        assert c.is_valid()

    def test_invalid_lat(self):
        from ai_engine.geographic_intelligence.gps_processor import GCSCoordinate
        c = GCSCoordinate(lat=999.0, lon=77.0)
        assert not c.is_valid()

    def test_anonymized_precision(self):
        from ai_engine.geographic_intelligence.gps_processor import GCSCoordinate
        c = GCSCoordinate(lat=12.9715999, lon=77.5945999)
        a = c.anonymized(precision=3)
        assert a.lat == 12.972
        assert a.lon == 77.595

    def test_in_india(self):
        from ai_engine.geographic_intelligence.gps_processor import GCSCoordinate, is_in_india
        assert is_in_india(GCSCoordinate(lat=12.97, lon=77.59))
        assert not is_in_india(GCSCoordinate(lat=40.71, lon=-74.0))


class TestHotspotAnalysis:
    def _pts(self, n=10):
        from ai_engine.geographic_intelligence.hotspot_analysis import IssuePoint
        return [IssuePoint(issue_id=i, lat=12.97 + i*0.001, lon=77.59 + i*0.001,
                severity="high", category="pothole", status="open",
                created_at=datetime.now(timezone.utc)) for i in range(n)]

    def test_hotspots_found(self):
        from ai_engine.geographic_intelligence.hotspot_analysis import find_hotspots
        hs = find_hotspots(self._pts(10), eps_km=0.3, min_pts=3)
        assert len(hs) >= 1

    def test_no_hotspots_few_points(self):
        from ai_engine.geographic_intelligence.hotspot_analysis import find_hotspots
        hs = find_hotspots(self._pts(2), eps_km=0.3, min_pts=5)
        assert hs == []

    def test_risk_score_range(self):
        from ai_engine.geographic_intelligence.hotspot_analysis import compute_risk_score
        s = compute_risk_score(0.8, 40, 0.9, 20)
        assert 0.0 <= s <= 1.0
