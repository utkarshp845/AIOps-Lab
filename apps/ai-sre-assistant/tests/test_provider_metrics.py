from fastapi.testclient import TestClient

from app.main import app
from app.provider_metrics import ProviderMetricsRegistry


def test_provider_metrics_aggregate_outcomes_latency_fallbacks_and_tokens():
    metrics = ProviderMetricsRegistry()

    metrics.observe(
        {
            "provider": "openai",
            "model": "approved-model",
            "attempted": True,
            "outcome": "success",
            "request_latency_ms": 125.0,
            "fallback_used": False,
            "fallback_reason": None,
            "usage": {"input_tokens": 120, "output_tokens": 30},
        }
    )
    metrics.observe(
        {
            "provider": "openai",
            "model": "approved-model",
            "attempted": True,
            "outcome": "failure",
            "request_latency_ms": 2500.0,
            "fallback_used": True,
            "fallback_reason": "provider_request_failed",
            "usage": {},
        }
    )

    rendered = metrics.render_prometheus()

    assert (
        'ai_sre_provider_analyses_total{provider="openai",model="approved-model",outcome="success"} 1'
        in rendered
    )
    assert (
        'ai_sre_provider_analyses_total{provider="openai",model="approved-model",outcome="failure"} 1'
        in rendered
    )
    assert (
        'ai_sre_provider_request_duration_seconds_bucket{provider="openai",model="approved-model",'
        'outcome="success",le="0.25"} 1'
    ) in rendered
    assert (
        'ai_sre_provider_request_duration_seconds_count{provider="openai",model="approved-model",'
        'outcome="failure"} 1'
    ) in rendered
    assert (
        'ai_sre_provider_fallbacks_total{provider="openai",model="approved-model",'
        'reason="provider_request_failed"} 1'
    ) in rendered
    assert (
        'ai_sre_provider_tokens_total{provider="openai",model="approved-model",direction="input"} 120'
        in rendered
    )
    assert (
        'ai_sre_provider_tokens_total{provider="openai",model="approved-model",direction="output"} 30'
        in rendered
    )


def test_provider_metrics_keep_label_values_bounded_and_ignore_sensitive_payload_fields():
    metrics = ProviderMetricsRegistry()

    metrics.observe(
        {
            "provider": "Bearer secret-provider-token",
            "model": "model-name",
            "attempted": False,
            "outcome": "unexpected-outcome",
            "request_latency_ms": 123.0,
            "fallback_used": True,
            "fallback_reason": "arbitrary-error-message",
            "prompt": "private incident evidence",
            "usage": {"input_tokens": -1, "output_tokens": True},
        }
    )

    rendered = metrics.render_prometheus()

    assert "secret-provider-token" not in rendered
    assert "private incident evidence" not in rendered
    assert 'outcome="unknown"' in rendered
    assert 'reason="other"' in rendered
    assert "ai_sre_provider_request_duration_seconds_count" not in rendered
    assert "ai_sre_provider_tokens_total{" not in rendered


def test_provider_metrics_endpoint_exposes_prometheus_contract():
    response = TestClient(app).get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "# TYPE ai_sre_provider_analyses_total counter" in response.text
    assert "# TYPE ai_sre_provider_request_duration_seconds histogram" in response.text
