"""
ai_engine/generative_ai/report_generator.py
Generates plain-text issue reports from structured data.
Does NOT call any paid LLM API. Uses template-based text composition.
Optionally integrates a local HuggingFace model for more natural language.
"""
from typing import Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class IssueReport:
    issue_id: int
    title: str
    category: str
    severity: str
    location_str: str
    ward: Optional[str]
    city: Optional[str]
    description: str
    days_open: int
    duplicate_count: int
    image_count: int
    status: str
    report_text: str
    recommended_actions: list[str]
    standard_reference: str
    generated_at: str = ""


SEVERITY_IMPACT = {
    "CRITICAL": "immediate public safety risk requiring emergency response",
    "HIGH": "significant risk to public health or safety; urgent intervention needed",
    "MEDIUM": "moderate impact on daily life and local infrastructure; scheduled repair needed",
    "LOW": "minor issue with limited impact; can be addressed in routine maintenance",
}

CATEGORY_IMPACT_PHRASES = {
    "pothole": "Vehicle damage, accident risk, and increased travel time for commuters",
    "road_damage": "Structural deterioration of road carriageway affecting all road users",
    "garbage": "Public health hazard, pest breeding, waterway blockage, and foul odour",
    "drainage": "Storm-water backflow, property damage, and waterborne disease risk",
    "waterlogging": "Road inaccessibility, traffic disruption, and drowning risk in heavy rain",
    "streetlight": "Night-time safety risk, increased crime vulnerability, traffic accident risk",
    "stray_animals": "Bite injury, rabies exposure, and traffic obstruction",
    "encroachment": "Reduced public space access and blocked pedestrian pathways",
    "other": "General civic infrastructure impact",
}

STANDARD_MAP = {
    "pothole": "IRC:73-2018",
    "road_damage": "IRC:73-2018 / IRC:SP:84",
    "garbage": "SWM Rules 2016",
    "drainage": "CPHEEO Manual 2013",
    "waterlogging": "CPHEEO Manual 2013 / NDMA Guidelines",
    "streetlight": "CEA Lighting Standards / IS:10500",
    "stray_animals": "ABC Rules 2023 / Prevention of Cruelty to Animals Act",
    "encroachment": "Municipal Corporation Act (state-specific)",
    "other": "Municipal Bylaws",
}


def build_report_text(
    title: str,
    category: str,
    severity: str,
    location_str: str,
    ward: Optional[str],
    city: Optional[str],
    description: str,
    days_open: int,
    duplicate_count: int,
    image_count: int,
    status: str,
) -> str:
    impact = SEVERITY_IMPACT.get(severity.upper(), "variable impact")
    cat_impact = CATEGORY_IMPACT_PHRASES.get(category, "general civic impact")
    standard = STANDARD_MAP.get(category, "Municipal Bylaws")

    dup_line = (
        f"This location has {duplicate_count} duplicate reports, confirming widespread citizen concern. "
        if duplicate_count >= 3 else ""
    )
    img_line = (
        f"{image_count} photographic evidence image(s) are attached to this report. "
        if image_count else ""
    )
    days_line = (
        f"The issue has been open for {days_open} day(s) without resolution. "
        if days_open > 7 else ""
    )

    return (
        f"PUBLIC ISSUE REPORT\n"
        f"{'='*40}\n"
        f"Title: {title}\n"
        f"Category: {category.replace('_',' ').title()} | Severity: {severity.upper()}\n"
        f"Location: {location_str}"
        f"{' | Ward: ' + ward if ward else ''}"
        f"{' | ' + city if city else ''}\n"
        f"Status: {status.upper()} | Opened: {days_open} days ago\n"
        f"{'='*40}\n\n"
        f"DESCRIPTION:\n{description[:300]}\n\n"
        f"ASSESSMENT:\n"
        f"This is classified as {severity.upper()} severity, indicating {impact}. "
        f"The primary community impact includes: {cat_impact}. "
        f"{days_line}{dup_line}{img_line}\n\n"
        f"STANDARD REFERENCE: {standard}\n"
        f"For officer action: please refer to the recommended repair steps in the system dashboard.\n"
    )


def generate_actions(
    category: str,
    severity: str,
    days_open: int,
    duplicate_count: int,
    nearby_high_risk: bool,
) -> list[str]:
    from ai_engine.generative_ai.prompt_templates import (
        IRC_73_2018, CPHEEO_DRAINAGE, SWM_RULES_2016, STREETLIGHT_GUIDE, STRAY_ANIMAL_RULES,
    )

    base_actions = {
        "pothole": [
            "Deploy engineering team to assess pothole dimensions (IRC:73-2018 thresholds).",
            "Apply emergency cold-patch if depth <40mm; hot-mix asphalt patch if >=40mm.",
            "Traffic marshalling and road signage during repair work.",
            "Post-repair inspection within 7 days to confirm durability.",
            "Escalate to zonal engineer if base course damage detected.",
        ],
        "road_damage": [
            "Survey full carriageway extent using image and site inspection.",
            "Classify damage type: surface crack / depression / rutting / ravelling.",
            "Issue work order for appropriate repair method per IRC:73-2018.",
            "Reroute traffic if structural integrity is compromised.",
            "Schedule seal coating after patch repair to extend road life.",
        ],
        "garbage": [
            "Send SWM collection team within 24 hours (SWM Rules 2016, Rule 20).",
            "Identify if site is a recurring dumping point; install CCTV signage if so.",
            "Segregate wet/dry/hazardous waste on collection.",
            "Spray disinfectant after clearing (vector control).",
            "Issue notice to dumpers under Municipal Solid Waste Act.",
        ],
        "drainage": [
            "Deploy de-silting team to clear blockage (CPHEEO Manual).",
            "Check if blockage is construction waste vs organic; route accordingly.",
            "Inspect upstream catchment for repeated source of blockage.",
            "Verify storm-water free flow after clearing (rain simulation if possible).",
            "Cover or pipe open drain section if within 15m of habitation.",
        ],
        "waterlogging": [
            "Identify waterlogging cause: drain blockage / poor gradient / encroachment.",
            "Deploy pumps for immediate relief if standing water >150mm.",
            "Clear all nearby drain inlets and gratings.",
            "Post monsoon risk signage if water is receding.",
            "Engineering survey for permanent gradient correction.",
        ],
        "streetlight": [
            "Dispatch electrician within 48 hours (urban SLA per CEA standards).",
            "Isolate power supply if exposed wiring is visible (CRITICAL safety).",
            "Replace faulty fixture; retrofit LED if non-functional.",
            "Verify pole stability – replace if lean >15 degrees.",
            "Confirm illumination level >= 10 lux after repair.",
        ],
        "stray_animals": [
            "Route to Animal Birth Control (ABC) centre and municipal vet (ABC Rules 2023).",
            "If aggressive: alert local police + vet for humane capture.",
            "Sterilise and vaccinate as per ABC protocol before release.",
            "Do NOT relocate sterilised dogs from territory (legal violation).",
            "Rabies alert to public health dept if bite incident confirmed.",
        ],
        "encroachment": [
            "Notify encroacher under Municipal Corporation Act.",
            "Grant 7-day notice period for voluntary removal.",
            "Escalate to Revenue/Taluk department if no response.",
            "Document with geotagged before-photos before action.",
            "Clear footpath to restore pedestrian access.",
        ],
    }

    actions = base_actions.get(category, [
        "Assign to relevant municipal department based on issue category.",
        "Physical verification by ward officer.",
        "Generate work order and assign a resolution deadline.",
        "Citizen notified of resolution status.",
    ])

    if nearby_high_risk:
        actions = ["[HIGH-RISK ZONE NEAR SCHOOL/HOSPITAL] Immediate escalation to zonal officer."] + actions

    if days_open > 14:
        actions = [f"[ESCALATION: {days_open} days overdue] Issue flagged to municipal commissioner dashboard."] + actions

    if duplicate_count >= 5:
        actions = [f"[PRIORITY: {duplicate_count} duplicate reports] Citizen demand signals high urgency."] + actions

    return actions[:6]  # max 6 actions


def generate_report(
    issue_id: int,
    title: str,
    category: str,
    severity: str,
    location_str: str,
    ward: Optional[str],
    city: Optional[str],
    description: str,
    days_open: int,
    duplicate_count: int,
    image_count: int,
    status: str,
    nearby_high_risk: bool = False,
) -> IssueReport:
    report_text = build_report_text(
        title, category, severity, location_str, ward, city,
        description, days_open, duplicate_count, image_count, status,
    )
    actions = generate_actions(category, severity, days_open, duplicate_count, nearby_high_risk)
    return IssueReport(
        issue_id=issue_id,
        title=title,
        category=category,
        severity=severity,
        location_str=location_str,
        ward=ward,
        city=city,
        description=description,
        days_open=days_open,
        duplicate_count=duplicate_count,
        image_count=image_count,
        status=status,
        report_text=report_text,
        recommended_actions=actions,
        standard_reference=STANDARD_MAP.get(category, "Municipal Bylaws"),
        generated_at=datetime.utcnow().isoformat(),
    )
