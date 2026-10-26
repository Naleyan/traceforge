from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_existing_product():
    response = client.get("/products/p1")
    assert response.status_code == 200
    assert response.json()["name"] == "Clavier"


def test_get_unknown_product_returns_404():
    response = client.get("/products/p999")
    assert response.status_code == 404