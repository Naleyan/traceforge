from fastapi import FastAPI, HTTPException
from observability import setup_logging          

app = FastAPI(title="Product Service")
setup_logging(app)

#Création du faux catalogue
PRODUCTS = {
    "p1": {"id": "p1", "name": "Clavier", "price": 49.90, "stock": 10},
    "p2": {"id": "p2", "name": "Souris", "price": 19.90, "stock": 0},
    "p3": {"id": "p3", "name": "Écran", "price": 189.00, "stock": 5},
}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/products/{product_id}")
def get_product(product_id: str):
    product = PRODUCTS.get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.get("/products")
def get_all_products():
    return list(PRODUCTS.values())
