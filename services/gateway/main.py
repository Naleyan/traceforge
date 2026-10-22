import os

import httpx
from fastapi import FastAPI, HTTPException

#Configuration lue depuis l'environnement, avec des valeurs par défaut
PRODUCT_URL = os.getenv("PRODUCT_URL", "http://localhost:8001")
TIMEOUT = httpx.Timeout(float(os.getenv("HTTP_TIMEOUT_SECONDS", "2.0")))

app = FastAPI(title="API Gateway")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/products/{product_id}")
async def get_product(product_id: str):
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{PRODUCT_URL}/products/{product_id}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Product service timed out")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Product service unreachable")

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Product not found")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Product service error")

    return response.json()