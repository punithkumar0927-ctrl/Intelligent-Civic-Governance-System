"""backend/tests/test_geographic.py"""
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
    client.post("/api/auth/register", json={"username":"geo","email":"geo@x.com","password":"password123"})
    r = client.post("/api/auth/login", data={"username":"geo@x.com","password":"password123"})
    return r.json()["access_token"]

def _h(t): return {"Authorization": f"Bearer {t}"}

class TestGeoPoints:
    def test_empty(self, client, auth_token):
        r = client.get("/api/geographic/points", headers=_h(auth_token))
        assert r.status_code == 200; assert isinstance(r.json(), list)

    def test_with_filter(self, client, auth_token):
        r = client.get("/api/geographic/points?city=Bengaluru&severity=high", headers=_h(auth_token))
        assert r.status_code == 200

    def test_no_auth(self, client):
        r = client.get("/api/geographic/points")
        assert r.status_code in (401, 403)

class TestHotspots:
    def test_empty(self, client, auth_token):
        r = client.get("/api/geographic/hotspots", headers=_h(auth_token))
        assert r.status_code == 200; assert isinstance(r.json(), list)

    def test_params(self, client, auth_token):
        r = client.get("/api/geographic/hotspots?eps_km=0.5&min_samples=3", headers=_h(auth_token))
        assert r.status_code == 200

class TestWards:
    def test_empty(self, client, auth_token):
        r = client.get("/api/geographic/wards", headers=_h(auth_token))
        assert r.status_code == 200

class TestNearby:
    def test_nearby(self, client, auth_token):
        r = client.get("/api/geographic/nearby?lat=12.97&lon=77.59&radius_km=1.0", headers=_h(auth_token))
        assert r.status_code == 200; assert isinstance(r.json(), list)

    def test_invalid_lat(self, client, auth_token):
        r = client.get("/api/geographic/nearby?lat=999&lon=77.59&radius_km=1.0", headers=_h(auth_token))
        assert r.status_code in (400, 422)
