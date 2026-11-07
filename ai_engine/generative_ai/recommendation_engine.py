"""
ai_engine/generative_ai/recommendation_engine.py
Maps issue context to evidence-based civic action recommendations.
All recommendations are sourced from Indian municipal engineering standards.
No LLM API calls are required; works fully offline.
"""
from dataclasses import dataclass
from typing import Optional
from ai_engine.generative_ai.report_generator import generate_actions, STANDARD_MAP


@dataclass
class Recommendation:
    issue_id: int
    category: str
    severity: str
    urgency: str                    # EMERGENCY | URGENT | SCHEDULED | ROUTINE
    actions: list[str]
    standard_ref: str
    sla_hours: int                  # expected response window in hours
    escalation_required: bool = False
    department: str = ""
    note: str = ""


CATEGORY_DEPARTMENT = {
    "pothole": "Public Works / Roads Division",
    "road_damage": "Public Works / Roads Division",
    "garbage": "Solid Waste Management (SWM) Department",
    "drainage": "Storm Water Drainage Division",
    "waterlogging": "Storm Water Drainage Division",
    "streetlight": "Electrical Department",
    "stray_animals": "Veterinary / ABC Centre",
    "encroachment": "Municipal Enforcement / Revenue Department",
    "other": "Ward Office – General Administration",
}

SLA_BY_SEVERITY = {
    "CRITICAL": 24,
    "HIGH": 72,
    "MEDIUM": 168,     # 7 days
    "LOW": 336,        # 14 days
}


def compute_urgency(
    severity: str,
    days_open: int,
    duplicate_count: int,
    nearby_high_risk: bool,
    category: str,
) -> str:
    if severity == "CRITICAL" or nearby_high_risk and severity == "HIGH":
        return "EMERGENCY"
    if severity == "HIGH" or duplicate_count >= 8 or (severity == "MEDIUM" and days_open > 30):
        return "URGENT"
    if severity == "MEDIUM" or days_open > 14 or duplicate_count >= 4:
        return "SCHEDULED"
    return "ROUTINE"


def get_recommendation(
    issue_id: int,
    category: str,
    severity: str,
    days_open: int = 0,
    duplicate_count: int = 0,
    nearby_high_risk: bool = False,
) -> Recommendation:
    urgency = compute_urgency(severity, days_open, duplicate_count, nearby_high_risk, category)
    actions = generate_actions(category, severity, days_open, duplicate_count, nearby_high_risk)
    sla = SLA_BY_SEVERITY.get(severity.upper(), 168)

    if urgency == "EMERGENCY":
        sla = min(sla, 24)
    elif urgency == "URGENT":
        sla = min(sla, 72)

    escalation = (
        days_open > SLA_BY_SEVERITY.get(severity.upper(), 168) // 24
        or duplicate_count >= 10
        or (nearby_high_risk and severity in ("HIGH", "CRITICAL"))
    )

    note = ""
    if escalation:
        note = (
            f"ESCALATION TRIGGERED: "
            f"{'days open > SLA. ' if days_open > SLA_BY_SEVERITY.get(severity.upper(), 168) // 24 else ''}"
            f"{'10+ duplicate reports. ' if duplicate_count >= 10 else ''}"
            f"{'High-risk zone proximity. ' if nearby_high_risk else ''}"
        )

    return Recommendation(
        issue_id=issue_id,
        category=category,
        severity=severity,
        urgency=urgency,
        actions=actions,
        standard_ref=STANDARD_MAP.get(category, "Municipal Bylaws"),
        sla_hours=sla,
        escalation_required=escalation,
        department=CATEGORY_DEPARTMENT.get(category, "Ward Office"),
        note=note,
    )
