import importlib.util
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]

# This test process uses SQLite, never the project's PostgreSQL database.
os.environ["DATABASE_URL"] = "sqlite://"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import sqlalchemy

_original_sqlalchemy_create_engine = sqlalchemy.create_engine

def _test_safe_create_engine(url, *args, **kwargs):
    if str(url).startswith("sqlite"):
        for setting in ("pool_size", "max_overflow", "pool_recycle"):
            kwargs.pop(setting, None)
        kwargs.setdefault("connect_args", {"check_same_thread": False})
        kwargs.setdefault("poolclass", StaticPool)
    return _original_sqlalchemy_create_engine(url, *args, **kwargs)

sqlalchemy.create_engine = _test_safe_create_engine

from shared.database import Base

sqlalchemy.create_engine = _original_sqlalchemy_create_engine


def load_service(module_name: str, service_dir_name: str):
    service_dir = ROOT / service_dir_name
    service_path = service_dir / "main.py"

    # Both services have a local module named "models".
    # Remove it between imports to prevent importing the wrong model.
    sys.modules.pop("models", None)
    sys.path.insert(0, str(service_dir))

    try:
        spec = importlib.util.spec_from_file_location(module_name, service_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(service_dir))
        sys.modules.pop("models", None)


order_app = load_service("retailops_test_order_main", "order_service")
inventory_app = load_service(
    "retailops_test_inventory_main", "inventory_service"
)

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)

# Replace each app's database connection with the isolated test database.
for service in (order_app, inventory_app):
    service.engine = test_engine
    service.SessionLocal = TestSessionLocal


@pytest.fixture(autouse=True)
def reset_test_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield


def test_order_health():
    with TestClient(order_app.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_and_retrieve_order():
    with TestClient(order_app.app) as client:
        response = client.post(
            "/orders",
            json={"sku": "SKU-TEST-01", "quantity": 2},
        )

        assert response.status_code == 201
        created = response.json()
        assert created["sku"] == "SKU-TEST-01"
        assert created["quantity"] == 2
        assert created["status"] == "CREATED"
        assert created["order_id"]
        assert created["created_at"]

        retrieved = client.get(f"/orders/{created['order_id']}")
        assert retrieved.status_code == 200
        assert retrieved.json()["order_id"] == created["order_id"]


def test_list_orders():
    with TestClient(order_app.app) as client:
        client.post(
            "/orders",
            json={"sku": "SKU-TEST-02", "quantity": 3},
        )
        response = client.get("/orders")

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert len(response.json()["orders"]) == 1


@pytest.mark.parametrize("quantity", [0, -1, 10001])
def test_order_rejects_invalid_quantity(quantity):
    with TestClient(order_app.app) as client:
        response = client.post(
            "/orders",
            json={"sku": "SKU-TEST-03", "quantity": quantity},
        )

    assert response.status_code == 422


def test_order_rejects_empty_sku():
    with TestClient(order_app.app) as client:
        response = client.post(
            "/orders",
            json={"sku": "", "quantity": 1},
        )

    assert response.status_code == 422


def test_missing_order_returns_404():
    with TestClient(order_app.app) as client:
        response = client.get("/orders/order-that-does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_inventory_health():
    with TestClient(inventory_app.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_inventory_is_seeded():
    with TestClient(inventory_app.app) as client:
        response = client.get("/inventory")

    assert response.status_code == 200
    assert response.json()["count"] == 3

    items = {item["sku"]: item for item in response.json()["items"]}
    assert items["SKU-1001"]["quantity"] == 100
    assert items["SKU-1002"]["quantity"] == 50
    assert items["SKU-1003"]["quantity"] == 25


def test_update_inventory_quantity():
    with TestClient(inventory_app.app) as client:
        response = client.put(
            "/inventory/SKU-1001",
            json={"quantity": 98},
        )

        assert response.status_code == 200
        assert response.json()["quantity"] == 98

        retrieved = client.get("/inventory/SKU-1001")
        assert retrieved.status_code == 200
        assert retrieved.json()["quantity"] == 98


@pytest.mark.parametrize("quantity", [-1, 1000001])
def test_inventory_rejects_invalid_quantity(quantity):
    with TestClient(inventory_app.app) as client:
        response = client.put(
            "/inventory/SKU-1001",
            json={"quantity": quantity},
        )

    assert response.status_code == 422


def test_inventory_rejects_missing_sku():
    with TestClient(inventory_app.app) as client:
        response = client.put(
            "/inventory/SKU-DOES-NOT-EXIST",
            json={"quantity": 5},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "SKU not found"


def test_inventory_seed_does_not_overwrite_existing_stock():
    with TestClient(inventory_app.app) as client:
        updated = client.put(
            "/inventory/SKU-1001",
            json={"quantity": 98},
        )
        assert updated.status_code == 200

    # A second application startup must not reset stock to 100.
    with TestClient(inventory_app.app) as client:
        response = client.get("/inventory/SKU-1001")

    assert response.status_code == 200
    assert response.json()["quantity"] == 98
