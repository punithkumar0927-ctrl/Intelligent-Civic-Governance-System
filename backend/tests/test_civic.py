import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, SessionLocal, engine
from app.models.user import User
from app.models.civic import CitizenReport  # noqa: F401

SQUARE = {
    "type": "Polygon",
    "coordinates": [[[77.5, 12.9], [77.6, 12.9], [77.6, 13.0], [77.5, 13.0], [77.5, 12.9]]],
}

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

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def _admin(client, email, username):
    token = _token(client, email, username)
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).one()
    user.role = "admin"
    db.commit()
    db.close()
    return token

def test_government_is_not_connected(client):
    token = _token(client, "gov@x.com", "gov")
    body = client.get("/api/civic/government", headers=_h(token)).json()
    assert body["reports_are_sent_automatically"] is False
    assert body["integrations"]["janaspandana_ipgrs"]["api_configured"] is False

def test_missing_boundary_is_pending_and_not_invented(client):
    token = _token(client, "citizen@x.com", "citizen1")
    created = client.post("/api/civic/reports", headers=_h(token), data={
        "description": "Water is collecting beside the school road.",
        "category": "Flooding and waterlogging",
        "latitude": "12.95",
        "longitude": "77.55",
        "gps_accuracy": "15",
        "citizen_gram_panchayat": "A name I typed",
    })
    assert created.status_code == 201
    body = created.json()
    assert body["verified_jurisdiction"]["status"] == "pending_verification"
    assert body["verified_jurisdiction"]["gram_panchayat"] is None
    assert body["citizen_location"]["gram_panchayat"] == "A name I typed"
    assert body["status"] == "Awaiting jurisdiction verification"
    assert body["government_delivery"] == "not_sent"
    assert body["official_reference"] is None
    assert body["reference"].startswith("NEXUS-")

def test_verified_polygon_routes_only_that_name(client):
    admin = _admin(client, "adminc@x.com", "adminc")
    boundary = client.post("/api/civic/boundaries", headers=_h(admin), json={
        "level": "gram_panchayat",
        "name": "Fixture Square GP",
        "source": "unit-test polygon",
        "geometry": SQUARE,
        "verified": True,
    })
    assert boundary.status_code == 201
    token = _token(client, "inside@x.com", "inside")
    created = client.post("/api/civic/reports", headers=_h(token), data={
        "description": "The village drain is blocked near the tank.",
        "category": "Drainage and sewage problems",
        "latitude": "12.95",
        "longitude": "77.55",
    })
    assert created.json()["verified_jurisdiction"]["gram_panchayat"] == "Fixture Square GP"
    assert created.json()["status"] == "Awaiting official forwarding"
    outside = client.post("/api/civic/reports", headers=_h(token), data={
        "description": "A streetlight is dark on the far side of town.",
        "category": "Broken streetlights",
        "latitude": "20",
        "longitude": "80",
    })
    assert outside.json()["verified_jurisdiction"]["gram_panchayat"] is None

def test_other_citizen_cannot_read_and_receipt_is_explicit(client):
    owner = _token(client, "owner@x.com", "owner")
    created = client.post("/api/civic/reports", headers=_h(owner), data={
        "description": "Garbage has piled beside the bus stop.",
        "category": "Garbage accumulation",
    }).json()
    other = _token(client, "other@x.com", "other")
    assert client.get(f"/api/civic/reports/{created['reference']}", headers=_h(other)).status_code == 404
    admin = _admin(client, "admin2@x.com", "admin2")
    boundary = client.post("/api/civic/boundaries", headers=_h(admin), json={
        "level": "district", "name": "Fixture District", "source": "unit-test polygon",
        "geometry": {"type": "Polygon", "coordinates": [[[77, 12], [78, 12], [78, 14], [77, 14], [77, 12]]]},
        "verified": True,
    }).json()
    official_token = _token(client, "off@x.com", "official")
    db = SessionLocal()
    official = db.query(User).filter(User.email == "off@x.com").one()
    official_id = official.id
    db.close()
    assigned = client.post("/api/civic/officials", headers=_h(admin), json={
        "user_id": official_id, "role": "zilla_official", "boundary_id": boundary["id"],
    })
    assert assigned.status_code == 200
    inside = client.post("/api/civic/reports", headers=_h(owner), data={
        "description": "The main road has a deep break near the tank.",
        "category": "Damaged roads and potholes",
        "latitude": "13",
        "longitude": "77.5",
    }).json()
    denied = client.post(f"/api/civic/reports/{inside['reference']}/actions", headers=_h(official_token), json={
        "action": "status", "status": "Submitted to authority",
    })
    assert denied.status_code == 422
    accepted = client.post(f"/api/civic/reports/{inside['reference']}/actions", headers=_h(official_token), json={
        "action": "confirm_receipt", "note": "Reviewed in NEXUS AI.",
    })
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "Submitted to authority"
    assert accepted.json()["government_delivery"] == "receipt_confirmed_by_nexus_official"
    assert "Janaspandana" in accepted.json()["history"][-1]["note"]
