"""tests/test_severity.py - Unit tests for severity prediction"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pytest


class TestFeatureExtraction:
    def test_severity_features_dataclass(self):
        from ai_engine.severity.feature_extraction import SeverityFeatures
        f = SeverityFeatures(
            edge_density=0.1, dark_ratio=0.05, texture_variance=0.3,
            damage_area_pct=0.05, bbox_count=2, mean_confidence=0.8,
            brightness_mean=128.0, contrast_range=60, aspect_ratio=1.2,
        )
        assert 0 <= f.edge_density <= 1
        assert f.bbox_count == 2

    def test_to_numpy_shape(self):
        from ai_engine.severity.feature_extraction import SeverityFeatures, to_numpy, FEATURE_NAMES
        f = SeverityFeatures(
            edge_density=0.1, dark_ratio=0.05, texture_variance=0.3,
            damage_area_pct=0.05, bbox_count=2, mean_confidence=0.8,
            brightness_mean=128.0, contrast_range=60, aspect_ratio=1.2,
        )
        arr = to_numpy(f)
        assert arr.shape == (len(FEATURE_NAMES),)
        assert arr.dtype == np.float32

    def test_feature_names_count(self):
        from ai_engine.severity.feature_extraction import FEATURE_NAMES
        assert len(FEATURE_NAMES) == 13


class TestHeuristicBaseline:
    def test_heuristic_critical(self):
        from ai_engine.severity.evaluate import heuristic_baseline
        # High edge_density + dark_ratio + damage_area -> should predict CRITICAL (3)
        X = np.array([[0.9, 0.5, 0.9, 0.9, 5, 0.95, 50, 200, 1.5, 0, 2, 2, 0.4]], dtype=np.float32)
        pred = heuristic_baseline(X)
        assert pred[0] == 3

    def test_heuristic_low(self):
        from ai_engine.severity.evaluate import heuristic_baseline
        X = np.array([[0.01, 0.001, 0.1, 0.005, 0, 0.5, 200, 20, 1.0, 0, 0, 0, 0.4]], dtype=np.float32)
        pred = heuristic_baseline(X)
        assert pred[0] == 0
