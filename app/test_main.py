import pytest
from main import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_index(client):
    resp = client.get("/")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["service"] == "cloud-deploy-platform"

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"

def test_ready(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
