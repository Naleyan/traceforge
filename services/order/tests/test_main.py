import pytest
from fastapi.testclient import TestClient

from main import ORDERS, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_orders():
    """Vide les commandes avant chaque test, pour que les tests ne s'influencent pas."""
    ORDERS.clear()


def create_order():
    return client.post("/orders", json={"product_id": "p1", "quantity": 2, "amount": 99.8})


def test_create_order_is_pending():
    response = create_order()
    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_update_status_to_paid():
    order_id = create_order().json()["id"]
    response = client.patch(f"/orders/{order_id}", json={"status": "paid"})
    assert response.status_code == 200
    assert response.json()["status"] == "paid"


def test_invalid_status_is_rejected():
    order_id = create_order().json()["id"]
    response = client.patch(f"/orders/{order_id}", json={"status": "shipped"})
    assert response.status_code == 422


def test_quantity_must_be_positive():
    response = client.post("/orders", json={"product_id": "p1", "quantity": 0, "amount": 10})
    assert response.status_code == 422


def test_unknown_order_returns_404():
    assert client.get("/orders/does-not-exist").status_code == 404