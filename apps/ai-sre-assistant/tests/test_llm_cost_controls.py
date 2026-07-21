import json

from fastapi.testclient import TestClient

from app.llm import LLMConfig, analyze_with_llm, build_user_prompt, cost_controls_summary, load_config
from app.main import app


client = TestClient(app)


def test_load_config_reads_llm_cost_controls(monkeypatch):
    monkeypatch.setenv("LLM_MAX_LOG_ENTRIES", "7")
    monkeypatch.setenv("LLM_MAX_PROMPT_CHARS", "2048")

    config = load_config()

    assert cost_controls_summary(config) == {
        "max_log_entries": 7,
        "max_prompt_chars": 2048,
    }


def test_llm_prompt_uses_recent_configured_log_window():
    config = LLMConfig(
        provider="openai",
        api_key="provider-key",
        base_url="https://example.invalid/v1",
        model="test-model",
        max_log_entries=2,
        max_prompt_chars=12000,
    )

    prompt, truncated = build_user_prompt(
        question="What happened?",
        logs=[
            {"message": "oldest-log"},
            {"message": "older-log"},
            {"message": "recent-log"},
            {"message": "newest-log"},
        ],
        rule_based_analysis={"summary": "rule-based summary"},
        config=config,
    )

    assert truncated is False
    assert "recent-log" in prompt
    assert "newest-log" in prompt
    assert "oldest-log" not in prompt
    assert "older-log" not in prompt


def test_llm_prompt_respects_budget_and_reports_usage(monkeypatch):
    captured = {}
    clock = iter([10.0, 10.125])

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [{"message": {"content": "bounded analysis"}}],
                "usage": {"prompt_tokens": 120, "completion_tokens": 30, "total_tokens": 150},
            }

    class FakeClient:
        def __init__(self, timeout):
            assert timeout == 30

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def post(self, url, headers, json):
            captured["prompt"] = json["messages"][1]["content"]
            return FakeResponse()

    monkeypatch.setattr("app.llm.httpx.Client", FakeClient)
    monkeypatch.setattr("app.llm.time.perf_counter", lambda: next(clock))
    config = LLMConfig(
        provider="openai",
        api_key="provider-key",
        base_url="https://example.invalid/v1",
        model="test-model",
        max_log_entries=5,
        max_prompt_chars=350,
    )

    result = analyze_with_llm(
        question="Investigate the latest failure",
        logs=[{"message": "x" * 2000}],
        rule_based_analysis={"summary": "y" * 1000},
        config=config,
    )

    assert result.analysis == "bounded analysis"
    assert result.notice == "LLM prompt was limited to 350 characters by cost controls."
    assert len(captured["prompt"]) <= 350
    assert result.telemetry == {
        "provider": "openai",
        "model": "test-model",
        "configured": True,
        "attempted": True,
        "outcome": "success",
        "request_latency_ms": 125.0,
        "fallback_used": False,
        "fallback_reason": None,
        "usage": {
            "reported": True,
            "input_tokens": 120,
            "output_tokens": 30,
            "total_tokens": 150,
        },
    }


def test_llm_failure_reports_safe_fallback_telemetry(monkeypatch):
    clock = iter([20.0, 20.025])

    class FailingClient:
        def __init__(self, timeout):
            assert timeout == 30

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def post(self, url, headers, json):
            raise RuntimeError("Bearer provider-secret failed at https://private-provider.invalid")

    monkeypatch.setattr("app.llm.httpx.Client", FailingClient)
    monkeypatch.setattr("app.llm.time.perf_counter", lambda: next(clock))
    config = LLMConfig(
        provider="private-provider",
        api_key="provider-key",
        base_url="https://private-provider.invalid/v1",
        model="private-model",
    )

    result = analyze_with_llm(
        question="Investigate password=question-secret",
        logs=[{"message": "Bearer log-secret"}],
        rule_based_analysis={"summary": "rule-based summary"},
        config=config,
    )

    assert result.analysis is None
    assert "provider-secret" not in result.notice
    assert result.telemetry["outcome"] == "failure"
    assert result.telemetry["request_latency_ms"] == 25.0
    assert result.telemetry["fallback_used"] is True
    assert result.telemetry["fallback_reason"] == "provider_request_failed"
    serialized = json.dumps(result.telemetry)
    assert "provider-key" not in serialized
    assert "private-provider.invalid" not in serialized
    assert "question-secret" not in serialized
    assert "log-secret" not in serialized


def test_api_response_reports_cost_controls_and_unconfigured_telemetry(tmp_path, monkeypatch):
    log_file = tmp_path / "demo-service.log"
    log_file.write_text('{"level":"INFO","message":"ok","status_code":200}\n', encoding="utf-8")
    monkeypatch.setenv("DEMO_SERVICE_LOG_PATH", str(log_file))
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("LLM_MAX_LOG_ENTRIES", "3")
    monkeypatch.setenv("LLM_MAX_PROMPT_CHARS", "4096")

    response = client.post("/ask", json={"question": "What happened?", "use_llm": True})

    assert response.status_code == 200
    body = response.json()
    assert body["analysis_mode"] == "rule-based"
    assert body["llm_cost_controls"] == {
        "max_log_entries": 3,
        "max_prompt_chars": 4096,
    }
    assert body["llm_telemetry"] == {
        "provider": "none",
        "model": None,
        "configured": False,
        "attempted": False,
        "outcome": "not_configured",
        "request_latency_ms": None,
        "fallback_used": True,
        "fallback_reason": "provider_not_configured",
        "usage": {
            "reported": False,
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
        },
    }
    assert "LLM provider is not configured" in body["llm_notice"]

def test_summarize_incident_reports_same_unconfigured_telemetry(tmp_path, monkeypatch):
    log_file = tmp_path / "demo-service.log"
    log_file.write_text('{"level":"INFO","message":"ok","status_code":200}\n', encoding="utf-8")
    monkeypatch.setenv("DEMO_SERVICE_LOG_PATH", str(log_file))
    monkeypatch.setenv("LLM_PROVIDER", "none")

    response = client.post(
        "/summarize-incident",
        json={"include_metrics": False, "use_llm": True},
    )

    assert response.status_code == 200
    telemetry = response.json()["llm_telemetry"]
    assert telemetry["provider"] == "none"
    assert telemetry["outcome"] == "not_configured"
    assert telemetry["attempted"] is False
    assert telemetry["fallback_reason"] == "provider_not_configured"
