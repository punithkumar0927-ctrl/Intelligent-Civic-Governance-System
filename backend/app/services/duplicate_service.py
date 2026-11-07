"""
duplicate_service.py — Multi-signal duplicate report detection.

Detection signals:
  1. Perceptual hash distance (phash)  → image similarity
  2. Text semantic similarity (sentence-transformers + FAISS) → description similarity
  3. Geo-proximity (Haversine distance) → location match
  4. Same category + time window → contextual match

Combined score > 0.75 → flagged as duplicate.
"""

import math
import numpy as np
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.issue import Issue, IssueStatus
from app.models.evidence import Evidence
from app.services.vision_service import hamming_distance

# ── Lazy-loaded globals ──────────────────────────────────────────────────────
_sentence_model = None
_faiss_index    = None
_text_store     = []   # list of {issue_id, text, category, lat, lon}

PHASH_THRESHOLD    = 10   # Hamming distance ≤ 10 (out of 256 bits) = likely same image
TEXT_SIM_THRESHOLD = 0.82  # Cosine similarity ≥ 0.82 = semantically similar
GEO_RADIUS_KM      = 0.3   # Within 300 meters = potentially same location
TIME_WINDOW_DAYS   = 30    # Only compare with reports from last N days


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)
    return R * 2 * math.asin(math.sqrt(a))


def _get_sentence_model():
    global _sentence_model
    if _sentence_model is not None:
        return _sentence_model
    try:
        from sentence_transformers import SentenceTransformer
        _sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("[duplicate_service] sentence-transformers loaded")
        return _sentence_model
    except Exception as exc:
        print(f"[duplicate_service] ST load failed: {exc}")
        return None


def _embed_text(text: str) -> Optional[np.ndarray]:
    model = _get_sentence_model()
    if model is None or not text.strip():
        return None
    emb = model.encode(text, normalize_embeddings=True)
    return np.array(emb, dtype=np.float32)


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


def check_duplicate(
    db: Session,
    issue: Issue,
    phash: Optional[str],
    detected_label: Optional[str],
    description: str,
    latitude: Optional[float],
    longitude: Optional[float],
) -> Tuple[bool, Optional[int]]:
    """
    Returns (is_duplicate: bool, duplicate_of_id: Optional[int]).
    Compares new issue against recent existing issues using multi-signal scoring.
    """
    from datetime import datetime, timezone, timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(days=TIME_WINDOW_DAYS)

    # Candidates: same category, recent, not self, not already duplicate
    candidates = (
        db.query(Issue)
        .filter(
            Issue.id != issue.id,
            Issue.category == issue.category,
            Issue.created_at >= cutoff,
            Issue.status != IssueStatus.DUPLICATE,
        )
        .limit(100)
        .all()
    )

    if not candidates:
        return False, None

    # Embed new description once
    new_emb = _embed_text(description) if description else None

    best_score   = 0.0
    best_dup_id  = None

    for cand in candidates:
        score = 0.0
        signals_used = 0

        # Signal 1: Image perceptual hash
        cand_ev = (
            db.query(Evidence)
            .filter(Evidence.issue_id == cand.id, Evidence.phash.isnot(None))
            .first()
        )
        if phash and cand_ev and cand_ev.phash:
            dist = hamming_distance(phash, cand_ev.phash)
            if dist <= PHASH_THRESHOLD:
                score += 0.45
            elif dist <= PHASH_THRESHOLD * 2:
                score += 0.20
            signals_used += 1

        # Signal 2: Text semantic similarity
        if new_emb is not None and cand.description:
            cand_emb = _embed_text(cand.description)
            if cand_emb is not None:
                sim = cosine_sim(new_emb, cand_emb)
                if sim >= TEXT_SIM_THRESHOLD:
                    score += 0.30
                elif sim >= 0.70:
                    score += 0.15
                signals_used += 1

        # Signal 3: Geo proximity
        if (latitude and longitude and
                cand.latitude and cand.longitude):
            dist_km = _haversine_km(latitude, longitude, cand.latitude, cand.longitude)
            if dist_km <= GEO_RADIUS_KM:
                score += 0.30
            elif dist_km <= GEO_RADIUS_KM * 3:
                score += 0.10
            signals_used += 1

        # Signal 4: Same detected label
        if detected_label and cand.ai_detected_label:
            if detected_label.lower() == cand.ai_detected_label.lower():
                score += 0.10

        if score > best_score:
            best_score  = score
            best_dup_id = cand.id

    # Threshold: 0.75+ with at least 2 signals = duplicate
    is_dup = best_score >= 0.75

    return is_dup, best_dup_id if is_dup else None


def build_faiss_index(db: Session) -> None:
    """
    Pre-build FAISS index for semantic duplicate search (optional optimization).
    Run periodically via background job in production.
    """
    try:
        import faiss
        model = _get_sentence_model()
        if model is None:
            return

        issues = db.query(Issue).filter(
            Issue.description.isnot(None),
            Issue.status != IssueStatus.DUPLICATE,
        ).limit(5000).all()

        texts = []
        ids   = []
        for iss in issues:
            if iss.description and iss.description.strip():
                texts.append(iss.description)
                ids.append(iss.id)

        if not texts:
            return

        embs = model.encode(texts, normalize_embeddings=True).astype(np.float32)
        dim  = embs.shape[1]
        index = faiss.IndexFlatIP(dim)   # inner product = cosine (normalized)
        index.add(embs)

        global _faiss_index, _text_store
        _faiss_index = index
        _text_store  = [{"issue_id": i, "text": t} for i, t in zip(ids, texts)]
        print(f"[duplicate_service] FAISS index built: {len(texts)} vectors")
    except Exception as exc:
        print(f"[duplicate_service] FAISS build error: {exc}")
