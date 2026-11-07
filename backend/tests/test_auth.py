"""
backend/tests/test_auth.py
Tests for /auth endpoints: register, login, me.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import get_db, engine
from app.models.user import User

# Override DB with test database
@pytest.fixture(autouse=True)
def override_db():
    Base = getattr(app, "Base", None)
    from app.database import Base as AppBase
    AppBase.metadata.create_all(bind=engine)
    yield
    AppBase.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    session = Session(engine)
    yield session
    session.close()


def _register(client, username="testuser", email="test@example.com", password="Testpass123"):
    return client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": password,
        "full_name": "Test User",
    })


def _login(client, email="test@example.com", password="Testpass123"):
    return client.post("/api/auth/login", data={"username": email, "password": password})


class TestRegister:
    def test_success(self, client):
        r = _register(client)
        assert r.status_code == 201
        data = r.json()
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "test@example.com"
        assert "id" in data["user"]
        assert data["user"]["role"] == "citizen"
        assert "hashed_password" not in data

    def test_duplicate_username(self, client):
        _register(client, username="dupuser", email="a@b.com")
        r = _register(client, username="dupuser", email="c@d.com")
        assert r.status_code in (400, 409)

    def test_invalid_email(self, client):
        r = _register(client, email="notanemail")
        assert r.status_code == 422

    def test_short_password(self, client):
        r = _register(client, password="short")
        assert r.status_code in (400, 422)


class TestLogin:
    def test_success(self, client):
        _register(client)
        r = _login(client)
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_wrong_password(self, client):
        _register(client)
        r = _login(client, password="wrongpassword")
        assert r.status_code == 401

    def test_unknown_user(self, client):
        r = _login(client, email="nobody@example.com")
        assert r.status_code == 401


class TestMe:
    def test_authenticated(self, client):
        _register(client)
        token = _login(client).json()["access_token"]
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["username"] == "testuser"

    def test_no_token(self, client):
        r = client.get("/api/auth/me")
        assert r.status_code in (401, 403)

    def test_invalid_token(self, client):
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert r.status_code in (401, 403)


class TestAccountRecovery:
    def test_verify_and_reset(self, client):
        created = _register(client, username="recover", email="recover@example.com").json()
        token = created["dev_verification_token"]
        verified = client.post("/api/auth/verify-email", json={"token": token})
        assert verified.status_code == 200

        forgot = client.post("/api/auth/forgot-password", json={"email": "recover@example.com"})
        assert forgot.status_code == 200
        assert "reset" in forgot.json()["detail"].lower()
        reset = client.post("/api/auth/reset-password", json={
            "token": forgot.json()["dev_token"],
            "password": "Newpass123",
        })
        assert reset.status_code == 200
        relogin = _login(client, email="recover@example.com", password="Newpass123")
        assert relogin.status_code == 200

        unknown = client.post("/api/auth/forgot-password", json={"email": "missing@example.com"})
        assert unknown.status_code == 200
        assert unknown.json()["dev_token"] is None
