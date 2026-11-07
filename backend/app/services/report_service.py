"""
report_service.py — orchestrates the full NEXUS AI analysis pipeline.

Steps:
  1. Vision  → detect issue type + confidence from uploaded image
  2. Severity → compute severity score from image features + metadata
  3. Duplicate → check FAISS + perceptual hash for near-duplicate reports
  4. Recommend → generate evidence-based recommendation text
  5. Persist   → write AI results back to Issue record
"""

import json
from typing import Optional
from sqlalchemy.orm import Session

from app.models.issue import Issue, SeverityLevel
from app.models.evidence import Evidence, EvidenceType
from app.schemas.schemas import AIAnalysisResult
from app.services.vision_service import detect_issue, compute_image_features
from app.services.severity_service import predict_severity
from app.services.duplicate_service import check_duplicate
from app.services.location_service import generate_recommendation


SEVERITY_THRESHOLDS = [
    (0.75, SeverityLevel.CRITICAL),
    (0.50, SeverityLevel.HIGH),
    (0.25, SeverityLevel.MEDIUM),
    (0.00, SeverityLevel.LOW),
]


def _score_to_level(score: float) -> SeverityLevel:
    for threshold, level in SEVERITY_THRESHOLDS:
        if score >= threshold:
            return level
    return SeverityLevel.LOW


async def analyze_and_save(db: Session, issue: Issue) -> AIAnalysisResult:
    """
    Run the complete AI analysis pipeline for an Issue.
    Called automatically after report creation, or via POST /analyze.
    """
    detected_label: Optional[str]   = None
    confidence:     Optional[float] = None
    image_features: dict            = {}
    phash:          Optional[str]   = None

    # ── Step 1: Vision ───────────────────────────────────────────────────────
    evidence_list = db.query(Evidence).filter(
        Evidence.issue_id == issue.id,
        Evidence.evidence_type.in_([EvidenceType.IMAGE_BEFORE, EvidenceType.IMAGE_AFTER]),
    ).all()

    for ev in evidence_list:
        try:
            result = detect_issue(ev.file_path)
            if not result:
                continue
            image_features = compute_image_features(ev.file_path)
            phash = result.get("phash")
            ev.phash = phash
            ev.ai_analysis = json.dumps(result)
            issue.ai_status = result.get("status")
            if result.get("status") == "completed" and (result.get("max_confidence") or 0) > 0.30:
                detected_label = result.get("top_label")
                confidence = result.get("max_confidence")
                ev.yolo_label = detected_label
                ev.yolo_confidence = confidence
            db.commit()
            break
        except Exception as exc:
            print(f"[vision] skip {ev.file_path}: {exc}")

    # ── Step 2: Severity Prediction ──────────────────────────────────────────
    severity_score = 0.0
    try:
        severity_score = predict_severity(
            category       = issue.category.value if issue.category else "other",
            detected_label = detected_label,
            confidence     = confidence,
            image_features = image_features,
            description    = issue.description or "",
            upvotes        = issue.upvotes,
        )
    except Exception as exc:
        print(f"[severity] fallback: {exc}")
        severity_score = 0.3   # conservative default

    severity_level = _score_to_level(severity_score)

    # ── Step 3: Duplicate Detection ──────────────────────────────────────────
    is_dup       = False
    dup_of_id    = None
    try:
        is_dup, dup_of_id = check_duplicate(
            db           = db,
            issue        = issue,
            phash        = phash,
            detected_label = detected_label,
            description    = issue.description or "",
            latitude       = issue.latitude,
            longitude      = issue.longitude,
        )
    except Exception as exc:
        print(f"[duplicate] skip: {exc}")

    # ── Step 4: Recommendation ───────────────────────────────────────────────
    recommendation = None
    try:
        recommendation = generate_recommendation(
            category       = issue.category.value if issue.category else "other",
            severity_level = severity_level.value,
            detected_label = detected_label,
        )
    except Exception as exc:
        print(f"[recommend] skip: {exc}")

    # ── Step 5: Persist ──────────────────────────────────────────────────────
    issue.ai_detected_label = detected_label
    issue.ai_confidence     = confidence
    issue.severity_score    = severity_score
    issue.severity          = severity_level
    issue.is_duplicate      = is_dup
    issue.ai_duplicate_of_id = dup_of_id
    issue.analysis_complete = True
    model_note = None
    if issue.ai_status == "MODEL_NOT_CONFIGURED":
        model_note = (
            "Road-damage weights are not configured, so no detection was produced. "
            "Severity below is a transparent rule-based estimate from the reported category and image features, "
            "not a physical depth or safety measurement."
        )
        recommendation = f"{model_note} {recommendation or ''}".strip()
    db.commit()
    db.refresh(issue)

    return AIAnalysisResult(
        issue_id           = issue.id,
        detected_label     = detected_label,
        confidence         = confidence,
        severity_score     = severity_score,
        severity_level     = severity_level,
        duplicate_detected = is_dup,
        duplicate_of_id    = dup_of_id,
        recommendation     = recommendation,
        analysis_complete  = True,
        detection_status   = issue.ai_status,
        model_note         = model_note,
    )
