"""
backend/tests/test_api.py
Integration tests for NEXUS AI backend API.

Run with:
    cd backend
    pytest tests/ -v --tb=short

Requires: PostgreSQL running, or use sqlite for testing (in-memory).
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use SQLite in-memory for tests (override DATABASE_URL before importing app)
TEST_DB_URL = "sqlite:///./test_nexus.db"
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["ENVIRONMENT"] = "development"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import Base, get_db, engine
from app.main import app

# Override DB for tests
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    engine.dispose()
    if os.path.exists("./test_nexus.db"):
        os.remove("./test_nexus.db")


client = TestClient(app)


# ── Test: Health ──────────────────────────────────────────────────────────────
class TestHealth:
    def test_health_returns_200(self):
        r = client.get("/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_readiness_returns_200(self):
        r = client.get("/api/health/ready")
        assert r.status_code == 200
        assert r.json()["ready"] is True


# ── Test: Auth ────────────────────────────────────────────────────────────────
class TestAuth:
    TEST_USER = {
        "username": "pytestuser",
        "email": "pytest@test.com",
        "password": "testpass123",
        "full_name": "Pytest User",
    }
    _token: str = ""

    def test_register_success(self):
        r = client.post("/api/auth/register", json=self.TEST_USER)
        assert r.status_code == 201
        data = r.json()
        assert "access_token" in data
        assert data["user"]["email"] == self.TEST_USER["email"]
        assert data["user"]["role"] == "citizen"
        TestAuth._token = data["access_token"]

    def test_register_duplicate_email(self):
        r = client.post("/api/auth/register", json={**self.TEST_USER, "username": "other"})
        assert r.status_code == 400
        assert "already registered" in r.json()["detail"].lower()

    def test_login_success(self):
        r = client.post("/api/auth/login",
                        data={"username": self.TEST_USER["email"],
                              "password": self.TEST_USER["password"]})
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_wrong_password(self):
        r = client.post("/api/auth/login",
                        data={"username": self.TEST_USER["email"],
                              "password": "wrongpassword"})
        assert r.status_code == 401

    def test_me_requires_auth(self):
        r = client.get("/api/auth/me")
        assert r.status_code == 401

    def test_me_with_token(self):
        r = client.get("/api/auth/me",
                       headers={"Authorization": f"Bearer {self._token}"})
        assert r.status_code == 200
        assert r.json()["email"] == self.TEST_USER["email"]


# ── Test: Reports ─────────────────────────────────────────────────────────────
class TestReports:
    _issue_id: int = 0
    token = TestAuth._token

    @classmethod
    def setup_class(cls):
        # Get fresh token
        r = client.post("/api/auth/login",
                        data={"username": "pytest@test.com", "password": "testpass123"})
        cls.token = r.json()["access_token"]

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def test_create_report_minimal(self):
        r = client.post(
            "/api/reports",
            headers=self._headers(),
            data={
                "title": "Test pothole near junction",
                "category": "pothole",
                "description": "Large dangerous pothole at main road",
                "city": "Bengaluru",
            },
        )
        assert r.status_code == 201, r.json()
        data = r.json()
        assert data["title"] == "Test pothole near junction"
        assert data["category"] == "pothole"
        assert data["status"] == "pending"
        TestReports._issue_id = data["id"]

    def test_create_report_invalid_category(self):
        r = client.post(
            "/api/reports",
            headers=self._headers(),
            data={"title": "test issue here", "category": "not_a_category"},
        )
        assert r.status_code == 422

    def test_create_report_title_too_short(self):
        r = client.post(
            "/api/reports",
            headers=self._headers(),
            data={"title": "ab", "category": "pothole"},
        )
        assert r.status_code == 422

    def test_list_reports(self):
        r = client.get("/api/reports", headers=self._headers())
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data

    def test_get_issue_by_id(self):
        r = client.get(f"/api/reports/{self._issue_id}", headers=self._headers())
        assert r.status_code == 200
        assert r.json()["id"] == self._issue_id

    def test_get_nonexistent_issue(self):
        r = client.get("/api/reports/99999", headers=self._headers())
        assert r.status_code == 404

    def test_upvote(self):
        r = client.post(f"/api/reports/{self._issue_id}/upvote", headers=self._headers())
        assert r.status_code == 200
        assert r.json()["upvotes"] >= 1

    def test_citizen_cannot_update_status(self):
        r = client.patch(
            f"/api/reports/{self._issue_id}",
            headers=self._headers(),
            json={"status": "resolved"},
        )
        assert r.status_code == 403


# ── Test: Analytics ───────────────────────────────────────────────────────────
class TestAnalytics:
    token = TestAuth._token

    @classmethod
    def setup_class(cls):
        r = client.post("/api/auth/login",
                        data={"username": "pytest@test.com", "password": "testpass123"})
        cls.token = r.json()["access_token"]

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def test_dashboard(self):
        r = client.get("/api/analytics/dashboard", headers=self._headers())
        assert r.status_code == 200
        data = r.json()
        assert "total_issues" in data
        assert "by_category" in data
        assert "geo_points" in data
        assert isinstance(data["geo_points"], list)

    def test_trends(self):
        r = client.get("/api/analytics/trends?months=6", headers=self._headers())
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 6


# ── Test: AI Services (unit, no DB) ──────────────────────────────────────────
class TestSeverityService:
    def test_rule_based_pothole(self):
        from app.services.severity_service import predict_severity
        score = predict_severity(
            category="pothole",
            detected_label="pothole",
            confidence=0.88,
            image_features={"edge_density": 0.25, "contrast": 90, "brightness": 120,
                            "damage_area_ratio": 0.4, "texture_variance": 600,
                            "saturation_mean": 70, "is_dark": False},
            description="Deep large pothole near school causing danger",
            upvotes=5,
        )
        assert 0.0 <= score <= 1.0
        assert score > 0.5   # pothole with danger keywords should be > 0.5

    def test_low_severity_short_desc(self):
        from app.services.severity_service import predict_severity
        score = predict_severity(
            category="park",
            detected_label=None,
            confidence=None,
            image_features={},
            description="Small issue",
            upvotes=0,
        )
        assert 0.0 <= score <= 1.0
        assert score < 0.5


class TestVisionService:
    def test_phash_returns_hex_string(self):
        from app.services.vision_service import compute_phash
        import cv2, numpy as np, tempfile, os
        # Create test image
        img = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            cv2.imwrite(f.name, img)
            h = compute_phash(f.name)
        os.unlink(f.name) if False else None
        assert isinstance(h, str)
        assert len(h) > 0

    def test_hamming_distance(self):
        from app.services.vision_service import hamming_distance
        assert hamming_distance("ff", "ff") == 0
        assert hamming_distance("ff", "00") == 8


class TestLocationService:
    def test_pothole_recommendation_critical(self):
        from app.services.location_service import generate_recommendation
        rec = generate_recommendation("pothole", "critical")
        assert "IRC" in rec or "immediate" in rec.lower()
        assert len(rec) > 50

    def test_generic_fallback(self):
        from app.services.location_service import generate_recommendation
        rec = generate_recommendation("unknown_category", "low")
        assert len(rec) > 20  # Returns generic fallback
