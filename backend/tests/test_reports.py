"""backend/tests/test_reports.py"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine
from app.database import Base

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine); yield; Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_token(client):
    client.post("/api/auth/register", json={"username":"rep","email":"rep@x.com","password":"password123"})
    r = client.post("/api/auth/login", data={"username":"rep@x.com","password":"password123"})
    return r.json()["access_token"]

def _h(tok): return {"Authorization": f"Bearer {tok}"}

class TestCreateReport:
    def test_success(self, client, auth_token):
        r = client.post("/api/reports", headers=_h(auth_token), data={
            "title": "Deep pothole near City Hospital gate",
            "description": "Large pothole causing traffic slowdowns",
            "category": "pothole",
            "latitude": "12.9716",
            "longitude": "77.5946",
            "city": "Bengaluru",
        })
        assert r.status_code in (200, 201)
        d = r.json(); assert d["title"]; assert "id" in d; assert d["status"] in ("pending", "open", "OPEN")

    def test_no_auth(self, client):
        r = client.post("/api/reports", data={"title":"x","description":"y","category":"pothole"})
        assert r.status_code in (401, 403)

    def test_missing_title(self, client, auth_token):
        r = client.post("/api/reports", headers=_h(auth_token), data={
            "description": "test", "category": "pothole", "latitude": "12.0", "longitude": "77.0",
        })
        assert r.status_code in (400, 422)

class TestListReports:
    def test_empty_list(self, client, auth_token):
        r = client.get("/api/reports", headers=_h(auth_token))
        assert r.status_code == 200; assert "items" in r.json()

    def test_filter_status(self, client, auth_token):
        r = client.get("/api/reports?status=pending", headers=_h(auth_token))
        assert r.status_code == 200

class TestGetReport:
    def test_not_found(self, client, auth_token):
        r = client.get("/api/reports/99999", headers=_h(auth_token))
        assert r.status_code == 404

    def test_get_existing(self, client, auth_token):
        created = client.post("/api/reports", headers=_h(auth_token), data={
            "title":"Test road damage report", "description":"Road broken",
            "category":"road_damage","latitude":"12.0","longitude":"77.0",
        }).json()
        r = client.get(f"/api/reports/{created['id']}", headers=_h(auth_token))
        assert r.status_code == 200; assert r.json()["id"] == created["id"]

class TestUpdateStatus:
    def test_officer_changes_status(self, client, auth_token):
        created = client.post("/api/reports", headers=_h(auth_token), data={
            "title":"Pothole on main road", "description":"Large pothole",
            "category":"pothole","latitude":"12.0","longitude":"77.0",
        }).json()
        r = client.patch(f"/api/reports/{created['id']}", headers=_h(auth_token),
            json={"status":"in_progress","note":"Work order issued"})
        assert r.status_code in (200, 403)  # 403 if officer role required


PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


class TestDeleteReport:
    def _create(self, client, token, title="Pothole beside the school gate"):
        return client.post("/api/reports", headers=_h(token), data={
            "title": title,
            "description": "Visible road damage",
            "category": "pothole",
            "latitude": "12.97",
            "longitude": "77.59",
        }, files={"image_before": ("hole.png", PNG, "image/png")}).json()

    def test_owner_deletes_report_and_file(self, client, auth_token):
        created = self._create(client, auth_token)
        evidence = client.get(f"/api/reports/{created['id']}/evidence", headers=_h(auth_token)).json()
        assert evidence
        deleted = client.delete(f"/api/reports/{created['id']}", headers=_h(auth_token))
        assert deleted.status_code == 200
        assert deleted.json()["deleted"] == 1
        assert client.get(f"/api/reports/{created['id']}", headers=_h(auth_token)).status_code == 404
        assert evidence[0]["file_name"]
        from app.api.reports import UPLOAD_DIR
        leftovers = list(UPLOAD_DIR.glob(f"issue{created['id']}_*"))
        assert leftovers == []

    def test_other_user_cannot_delete(self, client, auth_token):
        created = self._create(client, auth_token)
        client.post("/api/auth/register", json={"username": "other", "email": "other@x.com", "password": "password123"})
        other = client.post("/api/auth/login", data={"username": "other@x.com", "password": "password123"}).json()["access_token"]
        denied = client.delete(f"/api/reports/{created['id']}", headers=_h(other))
        assert denied.status_code == 403
        assert client.get(f"/api/reports/{created['id']}", headers=_h(auth_token)).status_code == 200

    def test_delete_all_keeps_other_users(self, client, auth_token):
        self._create(client, auth_token, "First owned road report")
        self._create(client, auth_token, "Second owned road report")
        client.post("/api/auth/register", json={"username": "keeper", "email": "keeper@x.com", "password": "password123"})
        keeper = client.post("/api/auth/login", data={"username": "keeper@x.com", "password": "password123"}).json()["access_token"]
        kept = self._create(client, keeper, "Keeper road report stays")
        result = client.post("/api/reports/delete", headers=_h(auth_token), json={"delete_all": True, "confirm": "DELETE ALL"})
        assert result.status_code == 200
        assert result.json()["deleted"] == 2
        mine = client.get("/api/reports?mine=true", headers=_h(auth_token))
        assert mine.json()["total"] == 0
        assert client.get(f"/api/reports/{kept['id']}", headers=_h(keeper)).status_code == 200

    def test_unauthenticated(self, client):
        assert client.delete("/api/reports/1").status_code in (401, 403)
