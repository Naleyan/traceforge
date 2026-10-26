import uuid

from fastapi import FastAPI
from pydantic import BaseModel, Field
from observability import setup_logging          

app = FastAPI(title="Payment Service")
setup_logging(app)

class PaymentRequest(BaseModel):
    order_id: str
    amount: float = Field(gt=0)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/payments", status_code=201)
def create_payment(payment: PaymentRequest):
    # Paiement simulé : toujours accepté pour l'instant.
    return {
        "payment_id": str(uuid.uuid4()),
        "order_id": payment.order_id,
        "amount": payment.amount,
        "status": "approved",
    }