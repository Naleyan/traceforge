from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_payment_is_approved():
    response = client.post("/payments", json={"order_id": "o1", "amount": 49.9})
    assert response.status_code == 201
    assert response.json()["status"] == "approved"


def test_amount_must_be_positive():
    response = client.post("/payments", json={"order_id": "o1", "amount": 0})
    assert response.status_code == 422