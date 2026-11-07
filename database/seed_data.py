"""Create a clearly labeled, deterministic NEXUS AI demo dataset.

Run from the project root:
    python database/seed_data.py
    python database/seed_data.py --reset-demo
"""

import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models.evidence import Evidence
from app.models.issue import Issue, IssueCategory, IssueStatus, SeverityLevel
from app.models.location import Location
from app.models.resolution import Resolution, VerificationStatus
from app.models.user import User

DEMO_MARKER = "SAMPLE DEMO DATA:"
DEMO_PASSWORD = os.getenv("NEXUS_DEMO_PASSWORD", "NexusDemo!2026")

CATEGORIES = [
    *( [IssueCategory.ROAD_DAMAGE] * 42 ),
    *( [IssueCategory.POTHOLE] * 24 ),
    *( [IssueCategory.GARBAGE] * 18 ),
    *( [IssueCategory.WATER_LEAK] * 12 ),
    *( [IssueCategory.DRAINAGE] * 8 ),
    *( [IssueCategory.SIDEWALK] * 8 ),
    *( [IssueCategory.STREETLIGHT] * 4 ),
    *( [IssueCategory.TRAFFIC_SIGN] * 4 ),
]
STATUSES = [
    *([IssueStatus.PENDING] * 12),
    *([IssueStatus.UNDER_REVIEW] * 14),
    *([IssueStatus.IN_PROGRESS] * 12),
    *([IssueStatus.RESOLUTION_SUBMITTED] * 56),
    *([IssueStatus.VERIFIED_RESOLVED] * 26),
]
SEVERITIES = [
    *([SeverityLevel.LOW] * 48),
    *([SeverityLevel.MEDIUM] * 60),
    *([SeverityLevel.HIGH] * 8),
    *([SeverityLevel.CRITICAL] * 4),
]
CITIES = [
    *([("Bengaluru", "Karnataka", 12.9716, 77.5946)] * 84),
    *([("Davangere", "Karnataka", 14.4644, 75.9218)] * 24),
    *([("Mysuru", "Karnataka", 12.2958, 76.6394)] * 12),
]
DEMO_USERS = (
    ("demo_citizen", "citizen@nexus-ai.local", "citizen"),
    ("demo_officer", "officer@nexus-ai.local", "officer"),
    ("demo_admin", "admin@nexus-ai.local", "admin"),
)
TITLES = {
    IssueCategory.ROAD_DAMAGE: "Cracked road surface near {place}",
    IssueCategory.POTHOLE: "Pothole reported near {place}",
    IssueCategory.GARBAGE: "Waste accumulation near {place}",
    IssueCategory.WATER_LEAK: "Water leak reported near {place}",
    IssueCategory.DRAINAGE: "Blocked drain reported near {place}",
    IssueCategory.SIDEWALK: "Footpath obstruction near {place}",
    IssueCategory.STREETLIGHT: "Streetlight issue near {place}",
    IssueCategory.TRAFFIC_SIGN: "Damaged traffic sign near {place}",
}
PLACES = (
    "MG Road", "Brigade Road", "Lalbagh Main Road", "Whitefield Main Road",
    "JP Nagar 7th Phase", "Davangere Market", "Hadadi Road", "Mysuru Palace",
    "Vijayanagar", "City Bus Stand",
)


def _get_or_create_users(db: Session) -> tuple[User, User, list[User]]:
    users = []
    for username, email, role in DEMO_USERS:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            username_owner = db.query(User).filter(User.username == username).first()
            if username_owner is not None:
                raise RuntimeError(
                    f"Cannot create demo account {username!r}: username is already in use."
                )
            user = User(
                username=username,
                email=email,
                full_name=f"Demo {role.title()}",
                hashed_password=hash_password(DEMO_PASSWORD),
                role=role,
                is_active=True,
                is_verified=False,
            )
            db.add(user)
            db.flush()
        users.append(user)
    return users[1], users[0], [users[0]]


def _clear_demo_issues(db: Session) -> None:
    issue_ids = [
        row[0]
        for row in db.query(Issue.id)
        .filter(Issue.description.like(f"{DEMO_MARKER}%"))
        .all()
    ]
    if not issue_ids:
        return
    db.query(Resolution).filter(Resolution.issue_id.in_(issue_ids)).delete(
        synchronize_session=False
    )
    db.query(Evidence).filter(Evidence.issue_id.in_(issue_ids)).delete(
        synchronize_session=False
    )
    db.query(Location).filter(Location.issue_id.in_(issue_ids)).delete(
        synchronize_session=False
    )
    db.query(Issue).filter(Issue.id.in_(issue_ids)).delete(
        synchronize_session=False
    )
    db.commit()


def seed_demo_data(db: Session, reset_demo: bool = False) -> int:
    existing = db.query(Issue.id).filter(
        Issue.description.like(f"{DEMO_MARKER}%")
    ).count()
    if existing and not reset_demo:
        print(
            f"[seed] Found {existing} demo reports; leaving them unchanged. "
            "Use --reset-demo to replace only NEXUS AI demo records."
        )
        return existing
    if reset_demo:
        _clear_demo_issues(db)

    officer, citizen, _ = _get_or_create_users(db)
    rng = random.Random(2026)
    categories = CATEGORIES.copy()
    statuses = STATUSES.copy()
    severities = SEVERITIES.copy()
    cities = CITIES.copy()
    rng.shuffle(categories)
    rng.shuffle(statuses)
    rng.shuffle(severities)
    rng.shuffle(cities)

    now = datetime.now(timezone.utc)
    issues: list[Issue] = []
    for index in range(120):
        category = categories[index]
        status = statuses[index]
        severity = severities[index]
        city, state, center_lat, center_lon = cities[index]
        created_at = now - timedelta(days=rng.randint(1, 180), hours=rng.randint(0, 23))
        verified = status == IssueStatus.VERIFIED_RESOLVED
        issue = Issue(
            title=f"[DEMO] {TITLES[category].format(place=rng.choice(PLACES))}",
            description=(
                f"{DEMO_MARKER} Synthetic portfolio record for {city}; "
                "not an official report, real repair, or government verification."
            ),
            category=category,
            status=status,
            severity=severity,
            severity_score={
                SeverityLevel.LOW: 0.18,
                SeverityLevel.MEDIUM: 0.42,
                SeverityLevel.HIGH: 0.68,
                SeverityLevel.CRITICAL: 0.91,
            }[severity],
            latitude=round(center_lat + rng.uniform(-0.035, 0.035), 6),
            longitude=round(center_lon + rng.uniform(-0.04, 0.04), 6),
            ward=f"Ward {rng.randint(1, 120)}",
            city=city,
            state=state,
            ai_detected_label=category.value,
            ai_confidence=round(rng.uniform(0.72, 0.97), 3),
            is_duplicate=False,
            analysis_complete=True,
            reporter_id=citizen.id,
            assigned_to=officer.id if status in (
                IssueStatus.IN_PROGRESS,
                IssueStatus.RESOLUTION_SUBMITTED,
                IssueStatus.VERIFIED_RESOLVED,
            ) else None,
            resolved_at=created_at + timedelta(days=rng.randint(2, 30)) if verified else None,
            upvotes=rng.randint(0, 24),
            created_at=created_at,
        )
        db.add(issue)
        db.flush()
        issues.append(issue)

        if status in (IssueStatus.RESOLUTION_SUBMITTED, IssueStatus.VERIFIED_RESOLVED):
            db.add(Resolution(
                issue_id=issue.id,
                verifier_id=officer.id if verified else None,
                verification_status=(
                    VerificationStatus.CONFIRMED_FIXED
                    if verified else VerificationStatus.NEEDS_REVIEW
                ),
                human_verified=verified,
                verified_at=now - timedelta(days=rng.randint(1, 30)) if verified else None,
                resolution_claimed_at=created_at,
                officer_note=(
                    "Sample/demo verification record; not an actual municipal action."
                ),
            ))

    for duplicate in issues[8:16]:
        duplicate.is_duplicate = True
        duplicate.ai_duplicate_of_id = issues[0].id

    db.commit()
    print(
        "[seed] Created 120 sample reports (38 active, 56 resolution submitted, "
        "26 marked as sample verified resolutions; 12 high/critical; 8 possible duplicates)."
    )
    print("[seed] All generated records are visibly labeled as synthetic demo data.")
    return len(issues)


def main() -> None:
    reset_demo = "--reset-demo" in sys.argv
    unknown_args = set(sys.argv[1:]) - {"--reset-demo"}
    if unknown_args:
        raise SystemExit(f"Unknown option(s): {', '.join(sorted(unknown_args))}")
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_data(db, reset_demo=reset_demo)
    print("Demo sign-in: demo_citizen / value of NEXUS_DEMO_PASSWORD (default: NexusDemo!2026)")


if __name__ == "__main__":
    main()
