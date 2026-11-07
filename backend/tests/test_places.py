"""Saved places and the Routes API configuration check."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def _token(client):
    client.post("/api/auth/register", json={
        "username": "mapper",
        "email": "mapper@example.com",
        "password": "Maptest123",
    })
    response = client.post("/api/auth/login", data={"username": "mapper@example.com", "password": "Maptest123"})
    return response.json()["access_token"]


def test_saved_place_round_trip(client):
    headers = {"Authorization": f"Bearer {_token(client)}"}
    created = client.post("/api/places", headers=headers, json={
        "name": "City hall",
        "address": "Example address",
        "latitude": 12.97,
        "longitude": 77.59,
        "category": "landmark",
    })
    assert created.status_code == 201
    listed = client.get("/api/places", headers=headers)
    assert listed.status_code == 200
    assert listed.json()[0]["name"] == "City hall"
    removed = client.delete(f"/api/places/{created.json()['id']}", headers=headers)
    assert removed.status_code == 204


def test_route_without_server_key(client):
    headers = {"Authorization": f"Bearer {_token(client)}"}
    response = client.post("/api/maps/route", headers=headers, json={
        "origin": {"latitude": 12.97, "longitude": 77.59},
        "destination": {"latitude": 13.0, "longitude": 77.6},
        "travel_mode": "DRIVE",
    })
    assert response.status_code == 503
    assert "GOOGLE_MAPS_SERVER_KEY" in response.json()["detail"]
