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

def test_create_product(client):
    r = client.post("/api/products", json={"name": "Widget", "price": 9.99, "category": "tools"})
    assert r.status_code == 201
    assert r.get_json()["name"] == "Widget"

def test_list_products_empty(client):
    r = client.get("/api/products")
    assert r.status_code == 200
    assert "products" in r.get_json()

def test_list_products_after_create(client):
    client.post("/api/products", json={"name": "Gadget"})
    r = client.get("/api/products")
    assert r.get_json()["count"] >= 1

def test_filter_by_category(client):
    client.post("/api/products", json={"name": "Hammer", "category": "tools"})
    client.post("/api/products", json={"name": "Pen", "category": "stationery"})
    r = client.get("/api/products?category=tools")
    assert r.status_code == 200
    for p in r.get_json()["products"]:
        assert p["category"] == "tools"

def test_get_product(client):
    r = client.post("/api/products", json={"name": "Bolt"})
    pid = r.get_json()["id"]
    r2 = client.get(f"/api/products/{pid}")
    assert r2.status_code == 200
    assert r2.get_json()["name"] == "Bolt"

def test_get_missing_product(client):
    r = client.get("/api/products/missing")
    assert r.status_code == 404

def test_update_product(client):
    r = client.post("/api/products", json={"name": "Screw", "price": 1.0})
    pid = r.get_json()["id"]
    r2 = client.put(f"/api/products/{pid}", json={"price": 2.5})
    assert r2.status_code == 200
    assert r2.get_json()["price"] == 2.5

def test_update_missing_product(client):
    r = client.put("/api/products/missing", json={"price": 1.0})
    assert r.status_code == 404

def test_product_has_id(client):
    r = client.post("/api/products", json={"name": "Nail"})
    assert "id" in r.get_json()

def test_product_default_category(client):
    r = client.post("/api/products", json={"name": "Unknown"})
    assert r.get_json()["category"] == "general"

def test_product_default_stock(client):
    r = client.post("/api/products", json={"name": "Item"})
    assert r.get_json()["stock"] == 0

def test_health_has_version(client):
    r = client.get("/health")
    assert "version" in r.get_json()

def test_health_has_uptime(client):
    r = client.get("/health")
    assert "uptime" in r.get_json()

def test_list_has_version(client):
    r = client.get("/api/products")
    assert "version" in r.get_json()

@pytest.mark.parametrize("i", range(25))
def test_bulk_create_and_retrieve(client, i):
    r = client.post("/api/products", json={"name": f"Product{i}",
                    "price": float(i), "category": "bulk"})
    assert r.status_code == 201
    pid = r.get_json()["id"]
    r2 = client.get(f"/api/products/{pid}")
    assert r2.status_code == 200
    assert r2.get_json()["name"] == f"Product{i}"
