import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.gps_photo import GpsPhoto  # noqa: F401

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

def _token(client, email, username):
    client.post("/api/auth/register", json={"username": username, "email": email, "password": "password123"})
    return client.post("/api/auth/login", data={"username": email, "password": "password123"}).json()["access_token"]

def _headers(token):
    return {"Authorization": f"Bearer {token}"}

def test_upload_requires_auth(client):
    response = client.post("/api/gps-photos", data={"captured_at": "2026-11-07T06:00:00Z"}, files={"image": ("a.png", PNG, "image/png")})
    assert response.status_code in (401, 403)

def test_owner_upload_list_download_delete(client):
    token = _token(client, "cam@x.com", "cam")
    created = client.post("/api/gps-photos", headers=_headers(token), data={
        "captured_at": "2026-11-07T06:00:00+00:00",
        "latitude": "12.9716",
        "longitude": "77.5946",
        "gps_accuracy": "12",
        "location_address": "Sample geocoded address",
    }, files={"image": ("road.png", PNG, "image/png")})
    assert created.status_code == 201
    body = created.json()
    assert body["latitude"] == 12.9716
    assert body["upload_status"] == "uploaded"
    listed = client.get("/api/gps-photos", headers=_headers(token))
    assert listed.json()["total"] == 1
    downloaded = client.get(f"/api/gps-photos/{body['id']}/file", headers=_headers(token))
    assert downloaded.status_code == 200
    assert downloaded.content.startswith(b"\x89PNG")
    other = _token(client, "othercam@x.com", "othercam")
    assert client.get(f"/api/gps-photos/{body['id']}/file", headers=_headers(other)).status_code == 404
    assert client.delete(f"/api/gps-photos/{body['id']}", headers=_headers(other)).status_code == 404
    assert client.delete(f"/api/gps-photos/{body['id']}", headers=_headers(token)).status_code == 200
    assert client.get("/api/gps-photos", headers=_headers(token)).json()["total"] == 0

def test_address_without_coordinates_is_not_stored(client):
    token = _token(client, "nocoord@x.com", "nocoord")
    created = client.post("/api/gps-photos", headers=_headers(token), data={
        "captured_at": "2026-11-07T06:00:00+00:00",
        "location_address": "Invented place",
    }, files={"image": ("road.png", PNG, "image/png")})
    assert created.status_code == 201
    assert created.json()["latitude"] is None
    assert created.json()["location_address"] is None

def test_demo_video_hidden_until_admin_upload(client):
    from app.api.demo_video import DEMO_DIR
    for name in ("nexus-demo.mp4", "manifest.json"):
        (DEMO_DIR / name).unlink(missing_ok=True)
    assert client.get("/api/demo-video").json()["available"] is False
    token = _token(client, "admincam@x.com", "admincam")
    denied = client.post("/api/demo-video", headers=_headers(token), files={"video": ("demo.mp4", b"0" * 2048, "video/mp4")})
    assert denied.status_code == 403
    db = SessionLocal()
    user = db.query(User).filter(User.email == "admincam@x.com").one()
    user.role = "admin"
    db.commit()
    db.close()
    uploaded = client.post("/api/demo-video", headers=_headers(token), files={"video": ("demo.mp4", b"0" * 2048, "video/mp4")})
    assert uploaded.status_code == 200
    assert uploaded.json()["available"] is True
    assert uploaded.json()["url"].endswith("/uploads/demo/nexus-demo.mp4")
    for name in ("nexus-demo.mp4", "manifest.json"):
        (DEMO_DIR / name).unlink(missing_ok=True)
