from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from shared.database import Base, SessionLocal, engine
from models import Order

from prometheus_fastapi_instrumentator import Instrumentator

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="RetailOps Order Service",
    description="Persistent retail order management portfolio service",
    version="2.0.0",
    lifespan=lifespan,
)


class OrderRequest(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    quantity: int = Field(gt=0, le=10000)


def serialize_order(order: Order) -> dict:
    created_at = order.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    return {
        "order_id": order.order_id,
        "sku": order.sku,
        "quantity": order.quantity,
        "status": order.status,
        "created_at": created_at.isoformat(),
    }


@app.get("/")
def root():
    return {"service": "order-service", "status": "running"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "order-service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/orders", status_code=201)
def create_order(request: OrderRequest):
    order = Order(
        order_id=str(uuid4()),
        sku=request.sku,
        quantity=request.quantity,
        status="CREATED",
    )

    with SessionLocal() as db:
        db.add(order)
        db.commit()
        db.refresh(order)
        return serialize_order(order)


@app.get("/orders")
def list_orders():
    with SessionLocal() as db:
        orders = db.scalars(
            select(Order).order_by(Order.created_at.desc())
        ).all()

        return {
            "count": len(orders),
            "orders": [serialize_order(order) for order in orders],
        }


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    with SessionLocal() as db:
        order = db.get(Order, order_id)

        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")

        return serialize_order(order)

Instrumentator().instrument(app).expose(
    app,
    endpoint="/metrics",
    include_in_schema=False,
)
