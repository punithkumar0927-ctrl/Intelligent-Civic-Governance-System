"""
ai_engine/resolution_verification/evaluate_verification.py
Evaluates repair verification accuracy against ground-truth labels.
Reads datasets/resolution_verification/verification_labels.csv.
"""
import csv
import json
from pathlib import Path
from collections import Counter
from ai_engine.resolution_verification.verify_repair import verify_repair

LABELS_FILE = Path("datasets/resolution_verification/verification_labels.csv")
RESULTS_FILE = Path("storage/verification_eval_results.json")

STATUS_MAP = {
    "fixed": "LIKELY_FIXED",
    "partially_fixed": "PARTIALLY_FIXED",
    "not_fixed": "NOT_FIXED",
    "needs_review": "NEEDS_REVIEW",
}

def load_labels(path: Path = LABELS_FILE) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows

def evaluate(labels: list[dict]) -> dict:
    tp = fp = tn = fn = 0
    results = []
    for row in labels:
        try:
            verdict = verify_repair(
                issue_id=int(row.get("issue_id", 0)),
                before_path=row["before_image"],
                after_path=row["after_image"],
            )
            predicted = verdict.status
            actual = STATUS_MAP.get(row["label"].strip().lower(), row["label"].strip().upper())
            correct = predicted == actual
            results.append({
                "issue_id": row.get("issue_id"),
                "predicted": predicted,
                "actual": actual,
                "confidence": verdict.confidence,
                "correct": correct,
            })
            if predicted == "LIKELY_FIXED" and actual == "LIKELY_FIXED": tp += 1
            elif predicted == "LIKELY_FIXED" and actual != "LIKELY_FIXED": fp += 1
            elif predicted != "LIKELY_FIXED" and actual == "LIKELY_FIXED": fn += 1
            else: tn += 1
        except Exception as e:
            results.append({"issue_id": row.get("issue_id"), "error": str(e)})

    total = tp + fp + tn + fn
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) else 0.0
    accuracy = (tp + tn) / total if total else 0.0

    return {
        "total": total,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "per_sample": results,
    }

def main():
    if not LABELS_FILE.exists():
        print(f"[evaluate] Labels file not found: {LABELS_FILE}")
        print("Run scripts/download_datasets.py first, or add rows manually.")
        return
    labels = load_labels()
    print(f"[evaluate] {len(labels)} labelled pairs loaded")
    report = evaluate(labels)
    print(json.dumps({k: v for k, v in report.items() if k != "per_sample"}, indent=2))
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(report, f, indent=2)
    print(f"[evaluate] Full report saved to {RESULTS_FILE}")

if __name__ == "__main__":
    main()
