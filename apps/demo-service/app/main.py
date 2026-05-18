from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request, Response

from app.logging_config import logger
from app.metrics import METRICS
from app.routes import router


app = FastAPI(
    title="demo-service",
    description="A small production-shaped service for learning AI infrastructure basics.",
    version="0.1.0",
)

app.include_router(router)


@app.middleware("http")
async def record_requests(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid4()))
    start = perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["x-request-id"] = request_id
        return response
    except Exception:
        logger.exception(
            "unhandled_request_error",
            extra={
                "event": "unhandled_request_error",
                "method": request.method,
                "path": request.url.path,
                "request_id": request_id,
            },
        )
        raise
    finally:
        duration_seconds = perf_counter() - start
        duration_ms = round(duration_seconds * 1000, 2)
        path = _route_template(request)

        METRICS.observe_http_request(
            method=request.method,
            path=path,
            status_code=status_code,
            duration_seconds=duration_seconds,
        )

        logger.info(
            "request_completed",
            extra={
                "event": "request_completed",
                "method": request.method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "request_id": request_id,
            },
        )


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=METRICS.render_prometheus(), media_type="text/plain")


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "path", request.url.path)
