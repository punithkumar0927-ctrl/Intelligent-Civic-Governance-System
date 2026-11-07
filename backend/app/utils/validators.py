"""
utils/validators.py — Input validation helpers for NEXUS AI.
"""

import re
from typing import Optional


# ── Coordinate validation ─────────────────────────────────────────────────────
def is_valid_latitude(lat: float) -> bool:
    return -90.0 <= lat <= 90.0


def is_valid_longitude(lon: float) -> bool:
    return -180.0 <= lon <= 180.0


def is_valid_coords(lat: Optional[float], lon: Optional[float]) -> bool:
    if lat is None or lon is None:
        return True  # coords are optional
    return is_valid_latitude(lat) and is_valid_longitude(lon)


def round_coords_privacy(lat: float, lon: float, decimals: int = 3) -> tuple[float, float]:
    """Round coords to protect reporter identity. 3dp ≈ 111m."""
    return round(lat, decimals), round(lon, decimals)


# ── String validation ─────────────────────────────────────────────────────────
def is_valid_issue_title(title: str) -> tuple[bool, str]:
    if not title or not title.strip():
        return False, "Title cannot be empty"
    if len(title.strip()) < 5:
        return False, "Title must be at least 5 characters"
    if len(title) > 200:
        return False, "Title must be 200 characters or fewer"
    # Reject all-numeric titles
    if title.strip().isdigit():
        return False, "Title must contain descriptive text, not just numbers"
    return True, ""


def is_valid_description(desc: Optional[str]) -> tuple[bool, str]:
    if desc and len(desc) > 2000:
        return False, "Description must be 2000 characters or fewer"
    return True, ""


def is_valid_pincode(code: str) -> bool:
    """Indian 6-digit PIN code."""
    return bool(re.match(r"^[1-9]\d{5}$", code.strip()))


def is_valid_phone(phone: str) -> bool:
    """Accepts +91-XXXXXXXXXX or 10-digit Indian mobile."""
    phone = phone.strip().replace(" ", "").replace("-", "")
    return bool(re.match(r"^(\+91)?[6-9]\d{9}$", phone))


# ── Content safety ────────────────────────────────────────────────────────────
# Reject reports that target named individuals (legal / defamation protection)
_INDIVIDUAL_TARGETING_PATTERNS = [
    r"\b mr\.?\s+\w+", r"\b mrs\.?\s+\w+", r"\b ms\.?\s+\w+",
    r"\b dr\.?\s+\w+", r"\b\s+\w+\s+(is corrupt|steals|scam|fraud|thief)\b",
]


def contains_person_accusation(text: str) -> bool:
    """
    Returns True if the description appears to accuse a named individual.
    NEXUS AI reports infrastructure issues, not people.
    """
    lower = text.lower()
    for pat in _INDIVIDUAL_TARGETING_PATTERNS:
        if re.search(pat, lower, re.IGNORECASE):
            return True
    return False


def sanitize_description(desc: str) -> str:
    """Strip potentially dangerous HTML/script from user description."""
    # Remove HTML tags
    clean = re.sub(r"<[^>]+>", "", desc)
    # Remove JavaScript: URLs
    clean = re.sub(r"javascript:", "", clean, flags=re.IGNORECASE)
    # Collapse multiple whitespace
    clean = re.sub(r"\s{3,}", "  ", clean)
    return clean.strip()
