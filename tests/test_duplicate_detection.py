"""tests/test_duplicate_detection.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import cv2
import pytest


class TestDHash:
    def test_dhash_output_length(self):
        from ai_engine.duplicate_detection.image_similarity import dhash
        img = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        h = dhash(img)
        assert len(h) == 256  # 16x16
        assert set(np.unique(h)) <= {0, 1}

    def test_identical_images_zero_distance(self):
        from ai_engine.duplicate_detection.image_similarity import dhash, hamming_distance
        img = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        h1 = dhash(img); h2 = dhash(img)
        assert hamming_distance(h1, h2) == 0

    def test_different_images_nonzero_distance(self):
        from ai_engine.duplicate_detection.image_similarity import dhash, hamming_distance
        img1 = np.zeros((64, 64, 3), dtype=np.uint8)
        img2 = np.ones((64, 64, 3), dtype=np.uint8) * 255
        # Add noise to make them structurally different
        rng = np.random.default_rng(42)
        img1 = (img1 + rng.integers(0, 128, img1.shape)).astype(np.uint8)
        img2 = (img2 + rng.integers(128, 255, img2.shape)).astype(np.uint8)
        h1 = dhash(img1); h2 = dhash(img2)
        assert hamming_distance(h1, h2) > 0


class TestGeoSimilarity:
    def test_same_point_score_1(self):
        from ai_engine.duplicate_detection.location_similarity import geo_similarity
        s = geo_similarity(12.9716, 77.5946, 12.9716, 77.5946)
        assert s == pytest.approx(1.0)

    def test_far_point_score_0(self):
        from ai_engine.duplicate_detection.location_similarity import geo_similarity
        s = geo_similarity(12.9716, 77.5946, 28.6139, 77.2090, max_radius_km=0.3)
        assert s == 0.0

    def test_composite_range(self):
        from ai_engine.duplicate_detection.location_similarity import location_score
        la = {"lat": 12.9716, "lon": 77.5946, "ward": "Ward 100", "city": "Bengaluru"}
        lb = {"lat": 12.9717, "lon": 77.5947, "ward": "Ward 100", "city": "Bengaluru"}
        result = location_score(la, lb)
        assert 0.0 <= result["composite"] <= 1.0


class TestFindDuplicates:
    def test_identical_is_duplicate(self):
        from ai_engine.duplicate_detection.find_duplicates import find_duplicates, NewIssue
        new = NewIssue(
            issue_id=999, title="Pothole at MG Road bus stop",
            description="Large pothole near MG Road bus stop, 50cm wide",
            category="pothole", lat=12.9756, lon=77.6068, ward="Ward 102",
        )
        existing = [{
            "id": 1, "title": "Pothole at MG Road bus stop",
            "description": "Large pothole near MG Road bus stop, 50cm wide",
            "category": "pothole", "lat": 12.9756, "lon": 77.6068,
        }]
        results = find_duplicates(new, existing, threshold=0.60)
        assert len(results) >= 1
        assert results[0].similarity_score >= 0.60
