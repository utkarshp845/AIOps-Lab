from fastapi.testclient import TestClient

from app.main import app
from app.metrics import METRICS


client = TestClient(app)


def setup_function():
    METRICS.reset()


def test_health_endpoint_returns_healthy_status():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "demo-service"}


def test_metrics_endpoint_returns_prometheus_text():
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "demo_service_http_requests_total" in response.text
    assert "demo_service_http_request_duration_seconds_bucket" in response.text


def test_metrics_normalize_dynamic_order_paths():
    client.get("/api/orders/ord-1001")

    response = client.get("/metrics")

    assert 'path="/api/orders/{order_id}"' in response.text
    assert "ord-1001" not in response.text


def test_metrics_include_simulation_counters():
    client.get("/simulate/error?probability=1.0")
    client.get("/simulate/latency?min_ms=0&max_ms=1")
    client.get("/simulate/memory-pressure?size_mb=1")

    response = client.get("/metrics")

    assert 'demo_service_simulated_errors_total{endpoint="/simulate/error",error_type="checkout_dependency_timeout"} 1' in response.text
    assert 'demo_service_simulated_latency_events_total{endpoint="/simulate/latency"} 1' in response.text
    assert 'demo_service_memory_pressure_events_total{endpoint="/simulate/memory-pressure"} 1' in response.text
    assert 'status_code="500"' in response.text
