import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "healthy"

def test_create_user(client):
    r = client.post("/api/users", json={"name": "Alice", "email": "alice@test.com"})
    assert r.status_code == 201
    assert r.get_json()["name"] == "Alice"

def test_list_users_empty(client):
    r = client.get("/api/users")
    assert r.status_code == 200
    assert "users" in r.get_json()

def test_list_users_after_create(client):
    client.post("/api/users", json={"name": "Bob"})
    r = client.get("/api/users")
    assert r.get_json()["count"] >= 1

def test_get_user(client):
    r = client.post("/api/users", json={"name": "Carol"})
    uid = r.get_json()["id"]
    r2 = client.get(f"/api/users/{uid}")
    assert r2.status_code == 200
    assert r2.get_json()["name"] == "Carol"

def test_get_missing_user(client):
    r = client.get("/api/users/nonexistent")
    assert r.status_code == 404

def test_delete_user(client):
    r = client.post("/api/users", json={"name": "Dave"})
    uid = r.get_json()["id"]
    r2 = client.delete(f"/api/users/{uid}")
    assert r2.status_code == 200
    assert r2.get_json()["deleted"] == uid

def test_delete_missing_user(client):
    r = client.delete("/api/users/nonexistent")
    assert r.status_code == 404

def test_user_has_id(client):
    r = client.post("/api/users", json={"name": "Eve"})
    assert "id" in r.get_json()

def test_user_has_email(client):
    r = client.post("/api/users", json={"name": "Frank", "email": "f@f.com"})
    assert r.get_json()["email"] == "f@f.com"

def test_health_has_version(client):
    r = client.get("/health")
    assert "version" in r.get_json()

def test_health_has_uptime(client):
    r = client.get("/health")
    assert "uptime" in r.get_json()

def test_list_has_version(client):
    r = client.get("/api/users")
    assert "version" in r.get_json()

def test_create_default_email(client):
    r = client.post("/api/users", json={"name": "NoEmail"})
    assert r.status_code == 201
    assert r.get_json()["email"] == ""

def test_create_no_body(client):
    r = client.post("/api/users", json={})
    assert r.status_code == 201
    assert r.get_json()["name"] == "unknown"

@pytest.mark.parametrize("i", range(25))
def test_bulk_create_and_retrieve(client, i):
    r = client.post("/api/users", json={"name": f"User{i}", "email": f"u{i}@test.com"})
    assert r.status_code == 201
    uid = r.get_json()["id"]
    r2 = client.get(f"/api/users/{uid}")
    assert r2.status_code == 200
    assert r2.get_json()["name"] == f"User{i}"
