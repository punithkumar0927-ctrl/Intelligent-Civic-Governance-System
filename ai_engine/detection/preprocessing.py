"""
ai_engine/detection/preprocessing.py
Image preprocessing pipeline for road-damage detection datasets.
Handles RDD2022 and generic urban issue images.
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class PreprocessConfig:
    target_size: tuple = (640, 640)
    clahe_clip: float = 2.5
    clahe_grid: int = 8
    denoise_strength: int = 3
    sharpen: bool = True
    augment: bool = False
    augment_prob: float = 0.3


def load_and_resize(path: str, cfg: PreprocessConfig) -> np.ndarray:
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    return cv2.resize(img, cfg.target_size, interpolation=cv2.INTER_AREA)


def enhance_contrast(img: np.ndarray, cfg: PreprocessConfig) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=cfg.clahe_clip, tileGridSize=(cfg.clahe_grid, cfg.clahe_grid))
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def denoise(img: np.ndarray, cfg: PreprocessConfig) -> np.ndarray:
    return cv2.fastNlMeansDenoisingColored(img, None, cfg.denoise_strength, cfg.denoise_strength, 7, 21)


def sharpen(img: np.ndarray) -> np.ndarray:
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(img, -1, kernel)


def augment_hsv(img: np.ndarray, h_gain=0.05, s_gain=0.3, v_gain=0.3) -> np.ndarray:
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(float)
    hsv[:, :, 0] = (hsv[:, :, 0] + np.random.uniform(-h_gain, h_gain) * 180) % 180
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1 + np.random.uniform(-s_gain, s_gain)), 0, 255)
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] * (1 + np.random.uniform(-v_gain, v_gain)), 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def random_flip(img: np.ndarray, labels: Optional[list] = None) -> tuple:
    if np.random.random() > 0.5:
        img = cv2.fliplr(img)
        if labels:
            labels = [[1 - x2, y1, 1 - x1, y2, cls] for x1, y1, x2, y2, cls in labels]
    if np.random.random() > 0.5:
        img = cv2.flip(img, 0)
        if labels:
            labels = [[x1, 1 - y2, x2, 1 - y1, cls] for x1, y1, x2, y2, cls in labels]
    return img, labels


def preprocess_image(path: str, cfg: PreprocessConfig = None) -> np.ndarray:
    cfg = cfg or PreprocessConfig()
    img = load_and_resize(path, cfg)
    img = enhance_contrast(img, cfg)
    if cfg.augment and np.random.random() < cfg.augment_prob:
        img = augment_hsv(img)
    if cfg.sharpen:
        img = sharpen(img)
    return img


def preprocess_batch(paths: list[str], cfg: PreprocessConfig = None) -> list[np.ndarray]:
    cfg = cfg or PreprocessConfig()
    results = []
    for p in paths:
        try:
            results.append(preprocess_image(p, cfg))
        except Exception as e:
            print(f"[preprocessing] Skip {p}: {e}")
    return results
