from datetime import datetime, timezone
from fastapi import FastAPI

from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title="Walmart RetailOps API",
    description="Retail operations DevOps portfolio simulation",
    version="1.0.0",
)

@app.get("/")
def root():
    return {
        "service": "retailops-api",
        "status": "running",
        "environment": "local",
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "retailops-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

Instrumentator().instrument(app).expose(
    app,
    endpoint="/metrics",
    include_in_schema=False,
)
