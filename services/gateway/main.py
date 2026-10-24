import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Configuration
PRODUCT_URL = os.getenv("PRODUCT_URL", "http://localhost:8001")
ORDER_URL = os.getenv("ORDER_URL", "http://localhost:8002")
PAYMENT_URL = os.getenv("PAYMENT_URL", "http://localhost:8003")
TIMEOUT = httpx.Timeout(float(os.getenv("HTTP_TIMEOUT_SECONDS", "2.0")))

app = FastAPI(title="API Gateway")


class OrderRequest(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)


# Outils 
async def call_service(method: str, url: str, service: str, json: dict | None = None):
    """Appelle un service et transforme les problèmes réseau en erreurs HTTP claires."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            return await client.request(method, url, json=json)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail=f"{service} service timed out")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail=f"{service} service unreachable")


async def set_order_status(order_id: str, status: str) -> dict:
    response = await call_service(
        "PATCH", f"{ORDER_URL}/orders/{order_id}", "Order", json={"status": status}
    )
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Order service error")
    return response.json()


async def mark_payment_failed(order_id: str) -> None:
    # « Best effort » : si cette mise à jour échoue aussi, on ne veut pas
    # masquer l'erreur de paiement d'origine, donc on ignore l'échec.
    try:
        await set_order_status(order_id, "payment_failed")
    except HTTPException:
        pass


# --- Routes ---
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/products/{product_id}")
async def get_product(product_id: str):
    response = await call_service("GET", f"{PRODUCT_URL}/products/{product_id}", "Product")
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Product not found")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Product service error")
    return response.json()


@app.post("/orders", status_code=201)
async def create_order(request: OrderRequest):
    # 1. Vérifier le produit et le stock
    product = await get_product(request.product_id)
    if product["stock"] < request.quantity:
        raise HTTPException(status_code=409, detail="Insufficient stock")
    amount = round(product["price"] * request.quantity, 2)

    # 2. Créer la commande (statut « pending »)
    response = await call_service(
        "POST", f"{ORDER_URL}/orders", "Order",
        json={"product_id": request.product_id, "quantity": request.quantity, "amount": amount},
    )
    if response.status_code != 201:
        raise HTTPException(status_code=502, detail="Order service error")
    order = response.json()

    # 3. Payer
    try:
        response = await call_service(
            "POST", f"{PAYMENT_URL}/payments", "Payment",
            json={"order_id": order["id"], "amount": amount},
        )
    except HTTPException:
        await mark_payment_failed(order["id"])
        raise  # on relance l'erreur d'origine (502 ou 504)
    if response.status_code != 201:
        await mark_payment_failed(order["id"])
        raise HTTPException(status_code=502, detail="Payment service error")

    # 4. Confirmer la commande
    return await set_order_status(order["id"], "paid")