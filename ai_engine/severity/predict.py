"""ai_engine/severity/predict.py — Standalone severity inference."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.services.severity_service import predict_severity

if __name__ == "__main__":
    score = predict_severity(
        category="pothole",
        detected_label="pothole",
        confidence=0.87,
        image_features={"edge_density": 0.22, "contrast": 85, "brightness": 110,
                        "damage_area_ratio": 0.45, "texture_variance": 800,
                        "saturation_mean": 60, "is_dark": False},
        description="Large deep pothole near school crossing causing accidents",
        upvotes=12,
    )
    print(f"Severity Score: {score}")
    level = "CRITICAL" if score >= 0.75 else "HIGH" if score >= 0.50 else "MEDIUM" if score >= 0.25 else "LOW"
    print(f"Severity Level: {level}")
