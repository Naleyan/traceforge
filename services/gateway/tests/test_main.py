import json

import httpx
import respx
from fastapi.testclient import TestClient

from main import ORDER_URL, PAYMENT_URL, PRODUCT_URL, app

client = TestClient(app)

PRODUCT = {"id": "p1", "name": "Clavier", "price": 49.90, "stock": 10}
ORDER = {"id": "o1", "product_id": "p1", "quantity": 2, "amount": 99.8, "status": "pending"}


def mock_product(stock=10):
    return respx.get(f"{PRODUCT_URL}/products/p1").mock(
        return_value=httpx.Response(200, json={**PRODUCT, "stock": stock})
    )


def mock_order_creation():
    return respx.post(f"{ORDER_URL}/orders").mock(return_value=httpx.Response(201, json=ORDER))


def mock_order_update(status):
    return respx.patch(f"{ORDER_URL}/orders/o1").mock(
        return_value=httpx.Response(200, json={**ORDER, "status": status})
    )


@respx.mock
def test_order_is_paid_when_everything_works():
    mock_product()
    mock_order_creation()
    payment = respx.post(f"{PAYMENT_URL}/payments").mock(
        return_value=httpx.Response(201, json={"status": "approved"})
    )
    mock_order_update("paid")

    response = client.post("/orders", json={"product_id": "p1", "quantity": 2})

    assert response.status_code == 201
    assert response.json()["status"] == "paid"
    # Le montant envoyé au paiement est calculé par la Gateway
    assert json.loads(payment.calls.last.request.content)["amount"] == 99.8


@respx.mock
def test_insufficient_stock_returns_409_and_creates_no_order():
    mock_product(stock=0)
    order_creation = mock_order_creation()

    response = client.post("/orders", json={"product_id": "p1", "quantity": 2})

    assert response.status_code == 409
    assert not order_creation.called


@respx.mock
def test_unknown_product_returns_404():
    respx.get(f"{PRODUCT_URL}/products/p999").mock(return_value=httpx.Response(404))

    response = client.post("/orders", json={"product_id": "p999", "quantity": 1})

    assert response.status_code == 404


@respx.mock
def test_payment_timeout_returns_504_and_marks_order_failed():
    mock_product()
    mock_order_creation()
    respx.post(f"{PAYMENT_URL}/payments").mock(side_effect=httpx.ConnectTimeout)
    order_update = mock_order_update("payment_failed")

    response = client.post("/orders", json={"product_id": "p1", "quantity": 2})

    assert response.status_code == 504
    assert json.loads(order_update.calls.last.request.content)["status"] == "payment_failed"


@respx.mock
def test_payment_unreachable_returns_502():
    mock_product()
    mock_order_creation()
    respx.post(f"{PAYMENT_URL}/payments").mock(side_effect=httpx.ConnectError)
    mock_order_update("payment_failed")

    response = client.post("/orders", json={"product_id": "p1", "quantity": 2})

    assert response.status_code == 502


@respx.mock
def test_payment_500_returns_502():
    mock_product()
    mock_order_creation()
    respx.post(f"{PAYMENT_URL}/payments").mock(return_value=httpx.Response(500))
    mock_order_update("payment_failed")

    response = client.post("/orders", json={"product_id": "p1", "quantity": 2})

    assert response.status_code == 502


def test_invalid_quantity_returns_422():
    response = client.post("/orders", json={"product_id": "p1", "quantity": 0})
    assert response.status_code == 422