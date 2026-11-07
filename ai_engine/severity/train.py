"""
ai_engine/severity/train.py
XGBoost Severity Model Training Script for NEXUS AI.

Training data sources:
  1. RDD2020 (Road Damage Detection 2020 Challenge) — severity labels
  2. Synthetic dataset generated via generate_synthetic_data() below
  3. Historical labelled reports (export from your running DB later)

Features:
  - Category encoding, detected label, confidence
  - Image features: edge_density, contrast, brightness, damage_area_ratio, etc.
  - Text features: description length, keyword flags
  - Social features: upvotes

Target: severity_score (0.0–1.0) — continuous
        severity_level (LOW/MEDIUM/HIGH/CRITICAL) — classification

Usage:
    python train.py [--synthetic] [--data ./datasets/severity_train.csv]

Output:
    severity_xgb.pkl → copy to ai_engine/models/severity_xgb.pkl
"""

import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import classification_report, mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import joblib

FEATURE_COLS = [
    "cat_enc", "label_enc", "confidence",
    "edge_density", "contrast", "brightness", "damage_area_ratio",
    "texture_variance", "saturation_mean",
    "desc_len", "has_critical_kw", "has_urgency_kw",
    "upvotes", "upvotes_log",
]

CATEGORY_MAP = {
    "pothole": 0.7, "road_damage": 0.6, "water_leak": 0.5,
    "drainage": 0.4, "garbage": 0.3, "streetlight": 0.5,
    "sidewalk": 0.4, "traffic_sign": 0.5, "park": 0.2,
    "building": 0.8, "power_line": 0.9, "other": 0.3,
}


def generate_synthetic(n: int = 5000, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic training data mimicking real infrastructure report patterns.
    Replace with real labelled data when available.
    """
    rng = np.random.default_rng(seed)
    cats = list(CATEGORY_MAP.keys())

    rows = []
    for _ in range(n):
        cat = rng.choice(cats)
        base_risk = CATEGORY_MAP[cat]
        confidence = rng.beta(5, 2) if rng.random() > 0.3 else 0.0
        edge_density = np.clip(rng.normal(base_risk * 0.5, 0.15), 0, 1)
        contrast = rng.uniform(30, 200) / 255.0
        brightness = rng.uniform(40, 220) / 255.0
        damage_ratio = np.clip(rng.beta(2, 5) * (base_risk + 0.3), 0, 1)
        texture_var = rng.exponential(0.3) * (0.5 + base_risk)
        saturation = rng.uniform(20, 200) / 255.0
        desc_len = rng.uniform(0, 1)
        has_critical = 1 if rng.random() < base_risk * 0.25 else 0
        has_urgency = 1 if rng.random() < base_risk * 0.50 else 0
        upvotes = int(rng.poisson(base_risk * 5))
        upvotes_log = np.log1p(upvotes) / np.log1p(100)

        # Composite severity (ground truth for supervised learning)
        score = (
            base_risk * 0.35 +
            damage_ratio * 0.25 +
            has_critical * 0.20 +
            has_urgency * 0.08 +
            confidence * 0.06 +
            edge_density * 0.04 +
            min(upvotes_log, 1.0) * 0.02
        ) + rng.normal(0, 0.05)
        score = float(np.clip(score, 0, 1))

        if score >= 0.75: level = 3
        elif score >= 0.50: level = 2
        elif score >= 0.25: level = 1
        else: level = 0

        rows.append({
            "cat_enc": base_risk, "label_enc": base_risk,
            "confidence": confidence,
            "edge_density": edge_density, "contrast": contrast,
            "brightness": brightness, "damage_area_ratio": damage_ratio,
            "texture_variance": texture_var, "saturation_mean": saturation,
            "desc_len": desc_len, "has_critical_kw": has_critical,
            "has_urgency_kw": has_urgency,
            "upvotes": min(upvotes / 50.0, 1.0), "upvotes_log": upvotes_log,
            "severity_score": score, "severity_level": level,
        })

    return pd.DataFrame(rows)


def train(data_path: str | None, synthetic: bool) -> None:
    if synthetic or data_path is None:
        print("[INFO] Using synthetic training data (5000 samples)")
        df = generate_synthetic(5000)
    else:
        print(f"[INFO] Loading training data from {data_path}")
        df = pd.read_csv(data_path)

    X = df[FEATURE_COLS].values
    y_score  = df["severity_score"].values
    y_level  = df["severity_level"].values.astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_level, test_size=0.20, random_state=42, stratify=y_level
    )

    # Train XGBoost classifier (4-class)
    clf = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        objective="multi:softprob",
        num_class=4,
        random_state=42,
        eval_metric="mlogloss",
        early_stopping_rounds=30,
    )
    clf.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=50,
    )

    # Evaluate
    y_pred = clf.predict(X_test)
    print("\n── Classification Report ──")
    print(classification_report(
        y_test, y_pred,
        target_names=["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    ))

    # Cross-validation
    cv_scores = cross_val_score(
        xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.05,
                          objective="multi:softprob", num_class=4, random_state=42),
        X, y_level, cv=5, scoring="f1_macro"
    )
    print(f"5-Fold CV F1 (macro): {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # Save model
    out_path = Path(__file__).parent.parent / "models" / "severity_xgb.pkl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, out_path)
    print(f"\n[DONE] Model saved → {out_path}")
    print("       Copy to backend/models/severity_xgb.pkl for use.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=None, help="CSV path (optional)")
    parser.add_argument("--synthetic", action="store_true", default=True)
    args = parser.parse_args()
    train(args.data, args.synthetic)
