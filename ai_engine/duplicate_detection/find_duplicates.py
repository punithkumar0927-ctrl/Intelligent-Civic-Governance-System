"""
ai_engine/duplicate_detection/find_duplicates.py
Multi-signal duplicate detection combining image hash, text embedding,
location proximity, and category match.
Composite score: phash(0.40) + text(0.25) + geo(0.25) + category(0.10)
Threshold >= 0.75 => probable duplicate.
"""
import math
from typing import Optional
from dataclasses import dataclass


@dataclass
class DuplicateCandidate:
    issue_id: int
    title: str
    category: str
    similarity_score: float
    image_sim: float
    text_sim: float
    geo_sim: float
    cat_match: float
    verdict: str  # "duplicate" | "related" | "unrelated"


@dataclass
class NewIssue:
    issue_id: int
    title: str
    description: str
    category: str
    lat: float
    lon: float
    ward: Optional[str] = None
    image_path: Optional[str] = None


THRESHOLD_DUPLICATE = 0.75
THRESHOLD_RELATED = 0.55

WEIGHT_IMAGE = 0.40
WEIGHT_TEXT = 0.25
WEIGHT_GEO = 0.25
WEIGHT_CAT = 0.10


def _category_match(cat_a: str, cat_b: str) -> float:
    return 1.0 if cat_a.strip().lower() == cat_b.strip().lower() else 0.0


def _image_similarity(new_img_path: Optional[str], existing_img_path: Optional[str]) -> float:
    if not new_img_path or not existing_img_path:
        return 0.0
    try:
        from ai_engine.duplicate_detection.image_similarity import compare_image_pairs
        result = compare_image_pairs(new_img_path, existing_img_path)
        return result.get("similarity", 0.0)
    except Exception:
        return 0.0


def _text_similarity(text_a: str, text_b: str) -> float:
    """Cosine similarity of sentence-transformer embeddings."""
    if not text_a.strip() or not text_b.strip():
        return 0.0
    try:
        from sentence_transformers import SentenceTransformer, util
        model = SentenceTransformer("all-MiniLM-L6-v2")
        emb_a = model.encode(text_a, convert_to_tensor=True)
        emb_b = model.encode(text_b, convert_to_tensor=True)
        return float(util.cos_sim(emb_a, emb_b).item())
    except ImportError:
        # Simple word-overlap fallback
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())
        if not words_a or not words_b:
            return 0.0
        jaccard = len(words_a & words_b) / len(words_a | words_b)
        return round(jaccard, 4)


def _geo_similarity(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    dist_km = R * 2 * math.asin(math.sqrt(a))
    max_r = 0.3
    return max(0.0, 1.0 - dist_km / max_r)


def compute_composite(
    img_sim: float,
    text_sim: float,
    geo_sim: float,
    cat_match: float,
) -> float:
    return round(
        WEIGHT_IMAGE * img_sim +
        WEIGHT_TEXT * text_sim +
        WEIGHT_GEO * geo_sim +
        WEIGHT_CAT * cat_match,
        4,
    )


def find_duplicates(
    new_issue: NewIssue,
    existing_issues: list[dict],  # [{"id", "title", "description", "category", "lat", "lon", "image_path"}]
    top_k: int = 5,
    threshold: float = THRESHOLD_DUPLICATE,
) -> list[DuplicateCandidate]:
    """
    Returns sorted list of DuplicateCandidate for the new_issue.
    """
    candidates = []

    for ex in existing_issues:
        img_sim = _image_similarity(new_issue.image_path, ex.get("image_path"))
        text_sim = _text_similarity(
            f"{new_issue.title} {new_issue.description}",
            f"{ex.get('title', '')} {ex.get('description', '')}",
        )
        geo_sim = _geo_similarity(new_issue.lat, new_issue.lon, ex.get("lat", 0), ex.get("lon", 0))
        cat_match = _category_match(new_issue.category, ex.get("category", ""))

        score = compute_composite(img_sim, text_sim, geo_sim, cat_match)

        if score >= THRESHOLD_RELATED:
            verdict = "duplicate" if score >= threshold else "related"
            candidates.append(DuplicateCandidate(
                issue_id=ex.get("id", 0),
                title=ex.get("title", ""),
                category=ex.get("category", ""),
                similarity_score=score,
                image_sim=round(img_sim, 4),
                text_sim=round(text_sim, 4),
                geo_sim=round(geo_sim, 4),
                cat_match=cat_match,
                verdict=verdict,
            ))

    return sorted(candidates, key=lambda x: -x.similarity_score)[:top_k]
