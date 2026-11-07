"""tests/test_resolution.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import cv2
import pytest
import tempfile


def make_test_images():
    """Create a before/after test pair using temporary files."""
    rng = np.random.default_rng(0)
    before = rng.integers(40, 200, (200, 300, 3), dtype=np.uint8)
    after = before.copy()
    # Add blur to simulate repair
    after[50:150, 100:200] = cv2.GaussianBlur(after, (21, 21), 0)[50:150, 100:200]
    _, bf = tempfile.mkstemp(suffix=".jpg"); cv2.imwrite(bf, before)
    _, af = tempfile.mkstemp(suffix=".jpg"); cv2.imwrite(af, after)
    return bf, af


class TestEdgeDensity:
    def test_density_range(self):
        from ai_engine.resolution_verification.damage_comparison import edge_density
        img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        d = edge_density(img)
        assert 0.0 <= d <= 1.0

    def test_uniform_image_zero_edges(self):
        from ai_engine.resolution_verification.damage_comparison import edge_density
        img = np.full((200, 200, 3), 128, dtype=np.uint8)
        assert edge_density(img) == pytest.approx(0.0)


class TestSSIM:
    def test_identical_images_ssim_1(self):
        from ai_engine.resolution_verification.damage_comparison import ssim_single
        img = np.random.randint(50, 200, (200, 200, 3), dtype=np.uint8)
        s = ssim_single(img, img)
        assert s > 0.99

    def test_random_vs_random_low_ssim(self):
        from ai_engine.resolution_verification.damage_comparison import ssim_single
        a = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        b = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        s = ssim_single(a, b)
        assert s < 0.3


class TestCompareImages:
    def test_compare_returns_expected_keys(self):
        from ai_engine.resolution_verification.compare_images import compare_images
        bf, af = make_test_images()
        result = compare_images(bf, af)
        for key in ["ssim_score", "edge_reduction_pct", "brightness_delta", "resolved_probability", "recommendation"]:
            assert key in result, f"Missing key: {key}"
        import os; os.unlink(bf); os.unlink(af)

    def test_repaired_image_probability(self):
        from ai_engine.resolution_verification.compare_images import compare_images
        bf, af = make_test_images()
        result = compare_images(bf, af)
        # Repaired (blurred) region should give non-zero probability
        assert result["resolved_probability"] > 0.0
        import os; os.unlink(bf); os.unlink(af)
