import asyncio
import os
import random

from fastapi import APIRouter, HTTPException, Query

from app.logging_config import get_log_path, logger
from app.metrics import METRICS


router = APIRouter()

ORDERS = {
    "ord-1001": {"id": "ord-1001", "item": "notebook", "status": "paid"},
    "ord-1002": {"id": "ord-1002", "item": "keyboard", "status": "packed"},
    "ord-1003": {"id": "ord-1003", "item": "monitor", "status": "shipped"},
}


@router.get("/health")
def health() -> dict:
    return {"status": "healthy", "service": "demo-service"}


@router.get("/ready")
def ready() -> dict:
    log_path = get_log_path()
    log_dir = log_path.parent
    return {
        "status": "ready",
        "service": "demo-service",
        "checks": {
            "log_path": str(log_path),
            "log_directory_exists": log_dir.exists(),
            "log_directory_writable": os.access(log_dir, os.W_OK),
        },
    }


@router.get("/api/orders")
def list_orders() -> dict:
    logger.info(
        "orders_listed",
        extra={"event": "orders_listed", "order_count": len(ORDERS), "endpoint": "/api/orders"},
    )
    return {"orders": list(ORDERS.values())}


@router.get("/api/orders/{order_id}")
def get_order(order_id: str) -> dict:
    order = ORDERS.get(order_id)
    if not order:
        logger.warning(
            "order_not_found",
            extra={
                "event": "order_not_found",
                "order_id": order_id,
                "endpoint": "/api/orders/{order_id}",
            },
        )
        raise HTTPException(status_code=404, detail={"message": "order not found", "order_id": order_id})

    logger.info(
        "order_fetched",
        extra={"event": "order_fetched", "order_id": order_id, "endpoint": "/api/orders/{order_id}"},
    )
    return {"order": order}


@router.get("/simulate/error")
def simulate_error(
    probability: float = Query(default=0.65, ge=0.0, le=1.0, description="Chance of returning HTTP 500."),
) -> dict:
    roll = random.random()
    if roll < probability:
        METRICS.record_simulated_error(
            endpoint="/simulate/error",
            error_type="checkout_dependency_timeout",
        )
        logger.error(
            "simulated_checkout_failure",
            extra={
                "event": "simulated_error",
                "error_type": "checkout_dependency_timeout",
                "endpoint": "/simulate/error",
                "probability": probability,
                "roll": round(roll, 4),
            },
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "simulated checkout dependency timeout",
                "hint": "This failure is intentional for the learning lab.",
            },
        )

    logger.info(
        "simulated_error_endpoint_recovered",
        extra={"event": "simulated_error_recovered", "endpoint": "/simulate/error", "roll": round(roll, 4)},
    )
    return {"status": "ok", "message": "the simulated dependency responded this time"}


@router.get("/simulate/latency")
async def simulate_latency(
    min_ms: int = Query(default=300, ge=0, le=5000),
    max_ms: int = Query(default=1500, ge=1, le=10000),
) -> dict:
    if min_ms > max_ms:
        raise HTTPException(status_code=400, detail="min_ms must be less than or equal to max_ms")

    latency_ms = random.randint(min_ms, max_ms)
    await asyncio.sleep(latency_ms / 1000)
    METRICS.record_simulated_latency(endpoint="/simulate/latency")
    log_method = logger.warning if latency_ms >= 1000 else logger.info
    log_method(
        "simulated_latency",
        extra={"event": "simulated_latency", "endpoint": "/simulate/latency", "latency_ms": latency_ms},
    )
    return {"status": "ok", "latency_ms": latency_ms}


@router.get("/simulate/memory-pressure")
def simulate_memory_pressure(size_mb: int = Query(default=12, ge=1, le=64)) -> dict:
    chunks = [bytearray(1024 * 1024) for _ in range(size_mb)]
    allocated_mb = sum(len(chunk) for chunk in chunks) // (1024 * 1024)
    METRICS.record_memory_pressure(endpoint="/simulate/memory-pressure")

    logger.warning(
        "simulated_memory_pressure",
        extra={
            "event": "simulated_memory_pressure",
            "endpoint": "/simulate/memory-pressure",
            "memory_mb": allocated_mb,
        },
    )
    return {
        "status": "ok",
        "allocated_mb": allocated_mb,
        "note": "Memory was allocated only for this request and then released.",
    }


@router.get("/simulate/log-event")
def simulate_log_event(
    event: str = Query(default="manual_operator_note"),
    level: str = Query(default="info", pattern="^(info|warning|error)$"),
) -> dict:
    log_method = {"info": logger.info, "warning": logger.warning, "error": logger.error}[level]
    log_method(
        event,
        extra={"event": event, "endpoint": "/simulate/log-event", "operator_generated": True},
    )
    return {"status": "logged", "event": event, "level": level}
