from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from shared.database import Base, SessionLocal, engine
from models import InventoryItem

app = FastAPI(
    title="RetailOps Inventory Service",
    description="Persistent retail inventory management portfolio service",
    version="2.0.0",
)

SEED_ITEMS = [
    {"sku": "SKU-1001", "name": "Everyday T-Shirt", "quantity": 100},
    {"sku": "SKU-1002", "name": "Running Shoes", "quantity": 50},
    {"sku": "SKU-1003", "name": "Travel Backpack", "quantity": 25},
]


class StockUpdate(BaseModel):
    quantity: int = Field(ge=0, le=1000000)


def serialize_item(item: InventoryItem) -> dict:
    return {
        "sku": item.sku,
        "name": item.name,
        "quantity": item.quantity,
    }


@app.on_event("startup")
def create_tables_and_seed_inventory():
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        for seed in SEED_ITEMS:
            if db.get(InventoryItem, seed["sku"]) is None:
                db.add(InventoryItem(**seed))

        db.commit()


@app.get("/")
def root():
    return {"service": "inventory-service", "status": "running"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "inventory-service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/inventory")
def list_inventory():
    with SessionLocal() as db:
        items = db.scalars(
            select(InventoryItem).order_by(InventoryItem.sku)
        ).all()

        return {
            "count": len(items),
            "items": [serialize_item(item) for item in items],
        }


@app.get("/inventory/{sku}")
def get_stock(sku: str):
    with SessionLocal() as db:
        item = db.get(InventoryItem, sku)

        if item is None:
            raise HTTPException(status_code=404, detail="SKU not found")

        return serialize_item(item)


@app.put("/inventory/{sku}")
def update_stock(sku: str, request: StockUpdate):
    with SessionLocal() as db:
        item = db.get(InventoryItem, sku)

        if item is None:
            raise HTTPException(status_code=404, detail="SKU not found")

        item.quantity = request.quantity
        db.commit()
        db.refresh(item)

        return serialize_item(item)
