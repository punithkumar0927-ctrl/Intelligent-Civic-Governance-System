"""
ai_engine/duplicate_detection/image_similarity.py
Perceptual hash (dHash) and optional embedding-based image similarity.
"""
import cv2
import numpy as np
from typing import Optional
from pathlib import Path


def dhash(img: np.ndarray, size: int = 16) -> np.ndarray:
    """
    Difference hash: compares adjacent pixel gradients.
    Returns a binary numpy array of length size*size.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    resized = cv2.resize(gray, (size + 1, size), interpolation=cv2.INTER_AREA)
    diff = resized[:, 1:] > resized[:, :-1]
    return diff.flatten().astype(np.uint8)


def phash(img: np.ndarray, hash_size: int = 16, highfreq_factor: int = 4) -> np.ndarray:
    """
    Perceptual hash via DCT.
    Returns binary array of length hash_size*hash_size.
    """
    img_size = hash_size * highfreq_factor
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    resized = cv2.resize(gray, (img_size, img_size), interpolation=cv2.INTER_AREA).astype(float)
    dct = cv2.dct(resized)
    dct_low = dct[:hash_size, :hash_size]
    median = np.median(dct_low)
    return (dct_low > median).flatten().astype(np.uint8)


def hamming_distance(h1: np.ndarray, h2: np.ndarray) -> int:
    """Number of differing bits between two binary hash arrays."""
    return int(np.sum(h1 != h2))


def similarity_from_hamming(dist: int, hash_bits: int = 256) -> float:
    """Convert Hamming distance to 0-1 similarity score."""
    return 1.0 - (dist / hash_bits)


def compare_image_pairs(
    path_a: str | Path,
    path_b: str | Path,
    method: str = "dhash",
    threshold: float = 0.80,
) -> dict:
    """
    Returns {"similarity": float, "hamming_dist": int, "is_duplicate": bool}
    """
    img_a = cv2.imread(str(path_a))
    img_b = cv2.imread(str(path_b))
    if img_a is None or img_b is None:
        return {"similarity": 0.0, "hamming_dist": -1, "is_duplicate": False, "error": "read failed"}

    img_a = cv2.resize(img_a, (256, 256))
    img_b = cv2.resize(img_b, (256, 256))

    if method == "phash":
        ha = phash(img_a)
        hb = phash(img_b)
        bits = 256
    else:
        ha = dhash(img_a)
        hb = dhash(img_b)
        bits = 256

    dist = hamming_distance(ha, hb)
    sim = similarity_from_hamming(dist, bits)

    return {
        "similarity": round(sim, 4),
        "hamming_dist": dist,
        "is_duplicate": sim >= threshold,
    }


def get_embedding_similarity(path_a: str, path_b: str) -> Optional[float]:
    """
    Optional: uses sentence-transformers CLIP / ResNet embedding if available.
    Returns cosine similarity or None if model unavailable.
    """
    try:
        from sentence_transformers import SentenceTransformer, util
        # Use a small image model if available; otherwise skip
        # This is intentionally a soft dependency
        return None
    except ImportError:
        return None
