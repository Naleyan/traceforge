import uuid
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from observability import setup_logging          

app = FastAPI(title="Order Service")
setup_logging(app)


ORDERS: dict[str, dict] = {}


class OrderCreate(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)   # strictement positif
    amount: float = Field(gt=0)


class StatusUpdate(BaseModel):
    status: Literal["pending", "paid", "payment_failed"]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/orders", status_code=201)
def create_order(order: OrderCreate):
    order_id = str(uuid.uuid4())
    ORDERS[order_id] = {"id": order_id, **order.model_dump(), "status": "pending"}
    return ORDERS[order_id]


@app.get("/orders")
def list_orders():
    return list(ORDERS.values())


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    if order_id not in ORDERS:
        raise HTTPException(status_code=404, detail="Order not found")
    return ORDERS[order_id]


@app.patch("/orders/{order_id}")
def update_status(order_id: str, update: StatusUpdate):
    if order_id not in ORDERS:
        raise HTTPException(status_code=404, detail="Order not found")
    ORDERS[order_id]["status"] = update.status
    return ORDERS[order_id]