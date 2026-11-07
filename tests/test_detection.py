"""tests/test_detection.py - Unit tests for the detection AI engine"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import numpy as np
from unittest.mock import MagicMock, patch


class TestPreprocessing:
    def test_preprocess_config_defaults(self):
        from ai_engine.detection.preprocessing import PreprocessConfig
        cfg = PreprocessConfig()
        assert cfg.target_size == (640, 640)
        assert cfg.clahe_clip == 2.5
        assert 0 < cfg.augment_prob < 1

    def test_sharpen_shape(self):
        from ai_engine.detection.preprocessing import sharpen
        img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        out = sharpen(img)
        assert out.shape == img.shape

    def test_augment_hsv_preserves_shape(self):
        from ai_engine.detection.preprocessing import augment_hsv
        img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        out = augment_hsv(img)
        assert out.shape == img.shape
        assert out.dtype == np.uint8


class TestPredict:
    @patch("ai_engine.detection.predict.YOLO")
    def test_predict_returns_dict(self, mock_yolo_cls):
        mock_model = MagicMock()
        mock_result = MagicMock()
        mock_result.boxes = MagicMock()
        mock_result.boxes.xyxy = np.array([[100, 100, 200, 200]])
        mock_result.boxes.conf = np.array([0.9])
        mock_result.boxes.cls = np.array([0])
        mock_result.__getitem__ = lambda self, i: mock_result
        mock_model.return_value = [mock_result]
        mock_model.names = {0: "pothole"}
        mock_yolo_cls.return_value = mock_model

        from ai_engine.detection.predict import detect_image
        result = detect_image("nonexistent.jpg", model=mock_model)
        assert "detections" in result or isinstance(result, (dict, list))
