"""
ai_engine/duplicate/similarity.py
Standalone duplicate detection with FAISS + sentence-transformers.

Usage:
    python similarity.py --query "large pothole near station" --top-k 5
"""

import argparse
import numpy as np
from typing import Optional


# Simulated report store (replace with real DB query in production)
SAMPLE_REPORTS = [
    {"id": 1, "text": "Large pothole on MG Road near bus stop causing two-wheeler accidents"},
    {"id": 2, "text": "Deep pothole at Indiranagar 100ft road junction dangerous for vehicles"},
    {"id": 3, "text": "Garbage not collected for 3 days in Koramangala 5th block street"},
    {"id": 4, "text": "Streetlight not working on 80ft road Indiranagar dark at night"},
    {"id": 5, "text": "Water pipeline leak flooding road near Jayanagar 4th block market"},
    {"id": 6, "text": "Open manhole on Sarjapur Road near school very dangerous for children"},
    {"id": 7, "text": "Pothole on Whitefield main road near IT park entrance getting bigger"},
    {"id": 8, "text": "Drain blocked near HSR Layout causing sewage overflow on road"},
]


def compute_embeddings(texts: list[str]) -> np.ndarray:
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return model.encode(texts, normalize_embeddings=True).astype(np.float32)
    except ImportError:
        # Fallback: random vectors for testing
        rng = np.random.default_rng(42)
        return rng.normal(0, 1, (len(texts), 384)).astype(np.float32)


def cosine_search(query: str, top_k: int = 5) -> list[dict]:
    query_emb = compute_embeddings([query])[0]
    doc_embs  = compute_embeddings([r["text"] for r in SAMPLE_REPORTS])

    scores = doc_embs @ query_emb   # cosine similarity (normalized vectors)
    top_indices = np.argsort(-scores)[:top_k]

    results = []
    for i in top_indices:
        results.append({
            "id": SAMPLE_REPORTS[i]["id"],
            "text": SAMPLE_REPORTS[i]["text"],
            "similarity": round(float(scores[i]), 4),
            "is_duplicate": scores[i] > 0.82,
        })
    return results


def build_faiss_index(texts: list[str], ids: list[int]) -> None:
    import faiss
    embs = compute_embeddings(texts)
    dim = embs.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embs)
    print(f"FAISS index built: {index.ntotal} vectors, dim={dim}")
    return index


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="Large deep pothole near school causing accidents")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    print(f"\nQuery: {args.query!r}\n")
    results = cosine_search(args.query, args.top_k)
    for r in results:
        flag = "🔴 DUPLICATE" if r["is_duplicate"] else "  ⚪"
        print(f"  {flag} [{r['similarity']:.3f}] id={r['id']}: {r['text']}")
