"""backend/tests/test_verification.py"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine); yield; Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_token(client):
    client.post("/api/auth/register", json={"username":"ver","email":"ver@x.com","password":"password123"})
    r = client.post("/api/auth/login", data={"username":"ver@x.com","password":"password123"})
    return r.json()["access_token"]

def _h(t): return {"Authorization": f"Bearer {t}"}

class TestPendingReview:
    def test_empty(self, client, auth_token):
        r = client.get("/api/verification/pending-review", headers=_h(auth_token))
        assert r.status_code in (200, 403)

class TestVerificationSummary:
    def test_summary(self, client, auth_token):
        r = client.get("/api/verification/summary", headers=_h(auth_token))
        assert r.status_code == 200; d = r.json()
        assert "total_pending" in d or "verification_rate" in d

class TestSubmitAfterPhoto:
    def test_nonexistent_issue(self, client, auth_token):
        import io
        r = client.post("/api/verification/issue/99999", headers=_h(auth_token),
            files={"file": ("test.jpg", io.BytesIO(b"not_an_image"), "image/jpeg")})
        assert r.status_code in (400, 404, 422)
