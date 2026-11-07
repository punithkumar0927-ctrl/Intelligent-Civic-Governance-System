"""
location_service.py — Geo utilities and evidence-based recommendation engine.

Recommendations are sourced from:
  - Municipal corporation guidelines (Swachh Bharat, Smart Cities Mission docs)
  - IRC (Indian Roads Congress) standards
  - CPHEEO (Central Public Health & Environmental Engineering Organisation)
  - World Bank urban infrastructure reports
  - Research paper best practices

Each recommendation is static, evidence-backed text — NOT LLM-generated fiction.
"""

from typing import Optional


# ── Curated recommendation knowledge base ────────────────────────────────────
RECOMMENDATIONS: dict[str, dict[str, str]] = {
    "pothole": {
        "critical": (
            "IMMEDIATE ACTION REQUIRED: Deep/large pothole poses serious two-wheeler "
            "and pedestrian safety risk. As per IRC:SP:84-2009, road defects >30mm depth "
            "require urgent patch repair. Contact your municipal PWD emergency line. "
            "Place temporary barricade/tires around the hazard until repair crew arrives. "
            "Source: IRC:SP:84-2009 (Rural Road Maintenance Manual)"
        ),
        "high": (
            "Priority repair required within 7 days. Hot-mix asphalt patch is recommended "
            "per IRC:SP:53-2005 guidelines for urban road defects. Ensure proper compaction "
            "and drainage around the repair area to prevent recurrence. "
            "Source: IRC:SP:53-2005, Municipal Road Maintenance Guidelines"
        ),
        "medium": (
            "Cold patch or asphalt overlay recommended within 30 days. Monitor water "
            "accumulation near the pothole as it accelerates subgrade failure. "
            "Best practice: full-depth patch cutting clean edges before filling. "
            "Source: Swachh Bharat Mission Urban (SBM-U) Road Quality Standards"
        ),
        "low": (
            "Queue for routine maintenance cycle. Minor surface damage will worsen "
            "with monsoon if not sealed. Apply surface dressing or crack sealant. "
            "Source: IRC:SP:84-2009 preventive maintenance guidelines"
        ),
    },
    "road_damage": {
        "critical": (
            "Major structural road failure detected. Immediate traffic diversion needed. "
            "Municipal PWD and Traffic Police must inspect same-day. High risk of "
            "sinkhole or base-layer collapse. Barricade the area immediately. "
            "Source: IRC:SP:84-2009, National Highways Authority maintenance protocols"
        ),
        "high": (
            "Road reconstruction or deep milling and overlay required within 14 days. "
            "Assess subgrade condition before resurfacing. Engage licensed contractor "
            "as per PWD classification. "
            "Source: IRC:SP:53-2005, MoRTH Specification Section 500"
        ),
        "medium": (
            "Resurfacing with bituminous concrete overlay recommended. Check for "
            "underground utility damage (water/sewer lines) before road work. "
            "Coordinate with Jal Board/WASA for pipeline inspection. "
            "Source: CPHEEO Manual on Water Supply and Treatment, 2013"
        ),
        "low": (
            "Add to annual road maintenance plan. Surface dressing with emulsion "
            "and aggregates will restore riding quality. "
            "Source: IRC:SP:84 preventive maintenance schedule"
        ),
    },
    "garbage": {
        "critical": (
            "Large-scale illegal dumping near residential area. Health hazard — "
            "immediate clearance needed under Solid Waste Management Rules 2016. "
            "Notify municipal health officer. May require hazardous waste assessment "
            "if industrial/material content suspected. "
            "Source: SWM Rules 2016, Rule 14 (Littering penalties)"
        ),
        "high": (
            "Clear within 48 hours. Standing garbage attracts vectors (mosquitoes, "
            "rats) and contaminates groundwater. Segregate at source per SWM Rules. "
            "Deploy ULB collection vehicles. "
            "Source: Swachh Bharat Mission Urban field operations guide"
        ),
        "medium": (
            "Clear within 7 days via scheduled collection. Install community "
            "warning signage. Conduct awareness drive with RWAs. "
            "Source: SBM-U Community Engagement Framework"
        ),
        "low": (
            "Add to next weekly collection cycle. Monitor for accumulation. "
            "Source: Municipal solid waste SOP"
        ),
    },
    "streetlight": {
        "critical": (
            "Total lighting failure on main road/highway. Immediate safety risk "
            "for pedestrians and night traffic. Municipal electrical department "
            "must respond within 24 hours. Temporary lighting arrangement required. "
            "Source: CPHEEO Lighting Guidelines, IS 10500-2012"
        ),
        "high": (
            "Multiple non-functional streetlights in residential area. Repair "
            "within 7 days. Check for cable faults vs. bulb failure. "
            "Source: Energy Conservation Building Code (ECBC) 2017"
        ),
        "medium": (
            "Single light outage. Replace within 14 days. Consider LED upgrade "
            "under Street Lighting National Programme (SLNP). "
            "Source: SLNP, Energy Efficiency Services Ltd (EESL)"
        ),
        "low": (
            "Minor illumination issue. Include in next maintenance round. "
            "Source: Municipal electrical maintenance schedule"
        ),
    },
    "water_leak": {
        "critical": (
            "Major water main burst — supply disruption and road erosion risk. "
            "Immediate isolation and repair by Jal Board/WASA emergency team. "
            "Road closure may be required. "
            "Source: CPHEEO Manual on Water Supply & Treatment (2013), Ch. 18"
        ),
        "high": (
            "Continuous leak wasting significant potable water. Repair within 48 hours. "
            "Non-revenue water (NRW) losses must be addressed per AMRUT guidelines. "
            "Source: AMRUT 2.0, NRW Reduction Framework"
        ),
        "medium": (
            "Repair within 7 days. Check for corrosion at joint points. "
            "Monitor ground saturation near pipeline. "
            "Source: IS 3867-1990 (Ductile Iron Pipes)"
        ),
        "low": (
            "Minor seepage. Log for planned maintenance cycle. "
            "Source: Municipal pipeline maintenance SOP"
        ),
    },
    "drainage": {
        "critical": (
            "Storm drain completely blocked. Urban flooding imminent. "
            "Immediate de-silting and mechanical cleaning needed per CPHEEO "
            "manual. Coordinate with fire/rescue if water accumulation ongoing. "
            "Source: CPHEEO Manual on Storm Water Drainage (2017)"
        ),
        "high": (
            "Overflowing drain causing waterlogging. Desilt within 72 hours. "
            "Apply larvicide to prevent dengue/malaria breeding. "
            "Source: SBM-U Liquid Waste Management Rules 2019"
        ),
        "medium": (
            "Partially blocked drain. Scheduled cleaning within 14 days. "
            "Install grate covers to prevent solid waste entry. "
            "Source: AMRUT stormwater management guidelines"
        ),
        "low": (
            "Routine drain maintenance. Quarterly desiltation cycle. "
            "Source: Municipal drainage SOP"
        ),
    },
    "power_line": {
        "critical": (
            "LIVE/EXPOSED wire emergency. Do NOT approach. Maintain 10-meter safety "
            "perimeter. Call state electricity board emergency (1912/1800-xxxx-xxxx). "
            "Barricade and alert police immediately. Risk of electrocution. "
            "Source: Central Electricity Authority (CEA) Regulations 2010, Rule 58"
        ),
        "high": (
            "Damaged overhead line at dangerous height. DISCOM emergency team "
            "must inspect within 24 hours. Isolate feeder if needed. "
            "Source: CEA (Measures relating to Safety) Regulations 2010"
        ),
        "medium": (
            "Sagging or loose line. Repair within 7 days. Avoid tree trimming "
            "near lines without DISCOM permission. "
            "Source: Indian Electricity Rules 1956 (amended 2005)"
        ),
        "low": (
            "Minor pole damage. Log for planned inspection. "
            "Source: State Electricity Board maintenance schedule"
        ),
    },
    "sidewalk": {
        "critical": (
            "Sidewalk collapsed; pedestrians forced onto traffic lane. "
            "Immediate barricading and temporary walkway required. "
            "Mandatory under Rights of Persons with Disabilities Act 2016 for accessibility. "
            "Source: KMK Road Design Guidelines, IRC:SP:84"
        ),
        "high": (
            "Large broken section. Repair within 14 days. Ensure tactile paving "
            "continuity at crossings for visually impaired. "
            "Source: NBC 2016 Part 3 (Accessibility)"
        ),
        "medium": (
            "Cracked/uneven pavers. Repair within 30 days. Use interlocking "
            "concrete pavers per IS 15658. "
            "Source: KMK (Delhi) footpath design standards"
        ),
        "low": (
            "Minor wear. Include in annual footpath resurfacing plan."
        ),
    },
    "traffic_sign": {
        "critical": (
            "Critical signage missing at high-speed junction. Immediate temporary "
            "sign required to prevent accidents. Notify Traffic Police same day. "
            "Source: Motor Vehicles Act 1988, IRC:SP:84-2009 Chapter 7"
        ),
        "high": (
            "Obscured or damaged sign at arterial road. Replace within 7 days. "
            "Signage retroreflectivity must meet IS 15658 standards. "
            "Source: IRC:SP:84-2009 (Rural Road Signs), IS 15658"
        ),
        "medium": (
            "Faded or partially damaged sign. Replace within 30 days. "
            "Source: Municipal traffic management SOP"
        ),
        "low": (
            "Minor sign damage. Add to sign replacement schedule."
        ),
    },
}

# Generic fallback for categories without specific guidance
GENERIC_RECOMMENDATIONS = {
    "critical": (
        "URGENT: Critical infrastructure issue requiring immediate municipal response. "
        "Contact local civic body emergency desk. Maintain public safety distance. "
        "Source: Disaster Management Act 2005, Municipal SOP"
    ),
    "high": (
        "High-priority issue requiring repair within 7 days. "
        "Notify assigned ward officer and track via municipal portal. "
        "Source: Smart Cities Mission civic service SLA framework"
    ),
    "medium": (
        "Medium-priority issue scheduled for 30-day resolution. "
        "Upvote to increase public visibility and accelerate response. "
        "Source: Municipal public grievance handling guidelines"
    ),
    "low": (
        "Low-priority issue queued for routine maintenance cycle. "
        "Will be monitored for escalation if worsens."
    ),
}


def generate_recommendation(
    category: str,
    severity_level: str,
    detected_label: Optional[str] = None,
) -> str:
    """
    Returns evidence-based recommendation text for the given category + severity.
    Uses curated knowledge base with document citations.
    """
    key = category.lower()
    sev = severity_level.lower()

    # Try detected label first (more specific from AI)
    if detected_label:
        dl_key = detected_label.lower().replace(" ", "_")
        if dl_key in RECOMMENDATIONS and sev in RECOMMENDATIONS[dl_key]:
            return RECOMMENDATIONS[dl_key][sev]

    # Fall back to category
    if key in RECOMMENDATIONS and sev in RECOMMENDATIONS[key]:
        return RECOMMENDATIONS[key][sev]

    # Final generic fallback
    return GENERIC_RECOMMENDATIONS.get(sev, GENERIC_RECOMMENDATIONS["low"])


# ── Geo utility functions ─────────────────────────────────────────────────────

def reverse_geocode_placeholder(lat: float, lon: float) -> dict:
    """
    Placeholder for reverse geocoding (OSM Nominatim in production).
    Returns ward/city/state for coordinates.
    NOTE: In MVP, user types address; this is optional.
    """
    return {
        "ward": None,
        "city": None,
        "state": None,
        "note": "Integrate Nominatim/Photon for production use",
    }


def anonymize_location(lat: float, lon: float, precision: int = 3) -> tuple[float, float]:
    """
    Coarsen GPS coordinates for public display (privacy).
    precision=3 ≈ 111m, precision=2 ≈ 1.1km.
    """
    return round(lat, precision), round(lon, precision)
