"""
ai_engine/generative_ai/prompt_templates.py
Prompt templates for evidence-grounded AI reports and recommendations.
All text is drawn from official standards (IRC, CPHEEO, SWM Rules).
NEVER asks an LLM to invent facts.
"""

SYSTEM_PROMPT_REPORT = """You are an urban infrastructure analyst.
Write a factual problem report using ONLY the provided evidence fields.
Do not add information not present in the data.
Do not name or accuse any individual.
Structure: [Location] -> [Problem] -> [Evidence] -> [Impact] -> [Recommended Action].
Keep the report under 200 words."""

SYSTEM_PROMPT_RECOMMENDATION = """You are an urban civic engineering assistant.
Given issue data, return a prioritised action list based on Indian municipal
engineering standards. Do NOT invent solutions not listed in the knowledge base.
Format as numbered steps. Maximum 5 steps."""

# IRC:73-2018: Pothole repair guideline
IRC_73_2018 = """
IRC:73-2018 Bituminous Road Maintenance Guidelines:
- Potholes >300mm diameter or >40mm depth require immediate patch repair.
- Emergency cold-patch (bitumen emulsion + aggregate) for potholes <0.5 m².
- Hot-mix asphalt patch required for potholes >0.5 m² or carriageway >50mm depression.
- Full-depth reclamation needed when base course is damaged.
- Seal coating after patch repair extends surface life by 3-5 years.
- Priority: arterial roads > highway connectors > residential streets.
"""

# CPHEEO Manual on Sewerage & Septic (drainage context)
CPHEEO_DRAINAGE = """
CPHEEO Manual on Sewerage and Septage Management (2013):
- Storm-water drains must be cleared before monsoon (April-May).
- Blockages >2m in covered drains require manual de-silting.
- Open drains within 15m of habitations must be covered or piped.
- Waterlogging >150mm depth for >6 hours is a public health risk.
- Drain outfall channels must be inspected monthly during monsoon.
"""

# SWM Rules 2016 context for garbage
SWM_RULES_2016 = """
Solid Waste Management Rules 2016 (India):
- Garbage must be segregated at source: wet, dry, domestic hazardous.
- Community waste accumulation >24 hours requires municipal clearance.
- Open dumping or burning is prohibited (Rule 20).
- Construction & demolition waste must be collected separately (C&D Rules 2016).
- Street sweeping: minimum once daily in commercial zones, alternate days residential.
"""

# Streetlight / electrical safety
STREETLIGHT_GUIDE = """
Central Electricity Authority (CEA) Standards for Street Lighting:
- Streetlights must provide minimum 10 lux on residential roads, 15 lux on arterials.
- Faulty or exposed wiring is an immediate electrocution risk (Report Level: CRITICAL).
- LED retrofit target: 60% of urban streetlights by 2025 (Smart Cities Mission).
- Poles leaning >15 degrees from vertical require immediate replacement.
- Response SLA for functional streetlight faults: 48 hours urban; 72 hours rural.
"""

# Stray animal management
STRAY_ANIMAL_RULES = """
Animal Birth Control (ABC) Rules 2023 (Government of India):
- Sterilisation and vaccination of stray dogs is the approved population management method.
- Relocation of sterilised dogs from their territory is prohibited.
- Complaints of aggressive/erratic animals should be routed to ABC centre + vet.
- Rabies vaccination drives: annual in endemic areas, immediately after any bite incident.
- Cattle: municipal bylaws govern grazing in urban zones; report to veterinary dept.
"""

# Category -> standard mapping
CATEGORY_STANDARDS = {
    "pothole": IRC_73_2018,
    "road_damage": IRC_73_2018,
    "drainage": CPHEEO_DRAINAGE,
    "waterlogging": CPHEEO_DRAINAGE,
    "garbage": SWM_RULES_2016,
    "streetlight": STREETLIGHT_GUIDE,
    "stray_animals": STRAY_ANIMAL_RULES,
}


def build_report_prompt(
    issue_title: str,
    issue_description: str,
    category: str,
    severity: str,
    location_str: str,
    image_count: int,
    days_open: int,
    duplicate_count: int,
    nearby_landmarks: list[str] = None,
) -> str:
    std = CATEGORY_STANDARDS.get(category, "")
    landmarks = ", ".join(nearby_landmarks[:3]) if nearby_landmarks else "not recorded"
    return f"""{SYSTEM_PROMPT_REPORT}

Issue Data:
- Title: {issue_title}
- Description: {issue_description[:200]}
- Category: {category}
- Severity: {severity}
- Location: {location_str}
- Nearby landmarks: {landmarks}
- Photos attached: {image_count}
- Days since reported: {days_open}
- Duplicate reports: {duplicate_count}

Relevant Standard:
{std[:500]}

Write the public issue report now."""


def build_recommendation_prompt(
    category: str,
    severity: str,
    location_str: str,
    ward: str,
    days_open: int,
    duplicate_count: int,
    nearby_high_risk: bool = False,
    issue_description: str = "",
) -> str:
    std = CATEGORY_STANDARDS.get(category, "")
    risk_note = "ALERT: This location is near a school or hospital." if nearby_high_risk else ""
    urgency = "URGENT" if days_open > 14 or duplicate_count > 5 else "NORMAL"
    return f"""{SYSTEM_PROMPT_RECOMMENDATION}

Context:
- Category: {category}
- Severity: {severity}
- Location: {location_str}
- Ward: {ward}
- Days open: {days_open}
- Duplicate reports: {duplicate_count}
- Urgency level: {urgency}
{risk_note}
Description: {issue_description[:150]}

Knowledge base (cite only from this):
{std}

Return a numbered list of up to 5 specific actionable steps."""
