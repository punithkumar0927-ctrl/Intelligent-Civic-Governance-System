"""
ai_engine/severity/evaluate.py
Evaluates the trained XGBoost severity model against a labelled test set.
Produces precision, recall, F1 per class and a confusion matrix.
"""
import json
import numpy as np
from pathlib import Path
from collections import Counter

SEVERITY_LABELS = {0: "LOW", 1: "MEDIUM", 2: "HIGH", 3: "CRITICAL"}
LABEL_TO_INT = {v: k for k, v in SEVERITY_LABELS.items()}

MODEL_PATH = Path("ai_engine/models/severity/severity_model.json")
TEST_DATA = Path("datasets/severity_prediction/severity_data.csv")
REPORT_PATH = Path("storage/severity_eval_report.json")


def load_model():
    try:
        import xgboost as xgb
        model = xgb.XGBClassifier()
        model.load_model(str(MODEL_PATH))
        return model
    except Exception as e:
        print(f"[severity/evaluate] Cannot load model: {e}")
        return None


def load_test_data() -> tuple:
    import csv
    if not TEST_DATA.exists():
        print(f"[severity/evaluate] Test file not found: {TEST_DATA}")
        return None, None
    features, labels = [], []
    with open(TEST_DATA, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                feats = [
                    float(row.get("edge_density", 0)),
                    float(row.get("dark_ratio", 0)),
                    float(row.get("texture_variance", 0)),
                    float(row.get("damage_area_pct", 0)),
                    int(row.get("bbox_count", 0)),
                    float(row.get("mean_confidence", 0)),
                    float(row.get("brightness_mean", 128)),
                    int(row.get("contrast_range", 50)),
                    float(row.get("aspect_ratio", 1.0)),
                    int(row.get("weather", 0)),
                    int(row.get("road_type", 0)),
                    int(row.get("traffic_level", 0)),
                    float(row.get("image_area_megapixels", 0.41)),
                ]
                label_str = row.get("severity", "medium").strip().upper()
                label = LABEL_TO_INT.get(label_str, 1)
                features.append(feats)
                labels.append(label)
            except Exception as e:
                print(f"[severity/evaluate] Row skip: {e}")
    return np.array(features, dtype=np.float32), np.array(labels, dtype=int)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    classes = sorted(set(y_true) | set(y_pred))
    metrics = {}
    for cls in classes:
        tp = int(np.sum((y_pred == cls) & (y_true == cls)))
        fp = int(np.sum((y_pred == cls) & (y_true != cls)))
        fn = int(np.sum((y_pred != cls) & (y_true == cls)))
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        metrics[SEVERITY_LABELS.get(cls, str(cls))] = {
            "tp": tp, "fp": fp, "fn": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": int(np.sum(y_true == cls)),
        }

    overall_acc = float(np.mean(y_true == y_pred))
    macro_f1 = float(np.mean([v["f1"] for v in metrics.values()]))
    weighted_f1 = float(
        sum(v["f1"] * v["support"] for v in metrics.values()) / len(y_true)
    ) if len(y_true) else 0.0

    # Confusion matrix
    n = len(classes)
    cm = [[0] * n for _ in range(n)]
    cls_list = sorted(set(y_true) | set(y_pred))
    cls_idx = {c: i for i, c in enumerate(cls_list)}
    for t, p in zip(y_true, y_pred):
        cm[cls_idx[t]][cls_idx[p]] += 1

    return {
        "overall_accuracy": round(overall_acc, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "per_class": metrics,
        "confusion_matrix": {
            "labels": [SEVERITY_LABELS.get(c, str(c)) for c in cls_list],
            "matrix": cm,
        },
    }


def heuristic_baseline(X: np.ndarray) -> np.ndarray:
    """Fallback when no trained model available: rule-based scoring."""
    edge_density = X[:, 0]
    dark_ratio = X[:, 1]
    damage_area = X[:, 3]
    scores = (0.4 * edge_density + 0.35 * dark_ratio + 0.25 * damage_area * 10)
    return np.where(scores >= 0.75, 3, np.where(scores >= 0.50, 2, np.where(scores >= 0.25, 1, 0)))


def main():
    model = load_model()
    X, y = load_test_data()
    if X is None or len(X) == 0:
        print("[severity/evaluate] No test data. Add rows to severity_data.csv.")
        return

    if model is not None:
        y_pred = model.predict(X)
        source = "xgboost_model"
    else:
        y_pred = heuristic_baseline(X)
        source = "heuristic_baseline"

    report = compute_metrics(y, y_pred)
    report["model_source"] = source
    report["n_samples"] = len(y)

    print(json.dumps({k: v for k, v in report.items() if k != "confusion_matrix"}, indent=2))

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"[severity/evaluate] Full report saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()
