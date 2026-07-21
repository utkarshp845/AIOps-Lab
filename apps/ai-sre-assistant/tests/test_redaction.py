import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.llm import LLMConfig, analyze_with_llm
from app.log_reader import read_recent_logs
from app.main import app
from app.redaction import REDACTED, redact_data, redact_text


client = TestClient(app)


def test_redact_data_handles_sensitive_fields_and_nested_values():
    value = {
        "authorization": "Bearer secret-token",
        "nested": {
            "clientSecret": "client-value",
            "message": "OPENAI_API_KEY=sk-example123456",
        },
    }

    assert redact_data(value) == {
        "authorization": REDACTED,
        "nested": {
            "clientSecret": REDACTED,
            "message": f"OPENAI_API_KEY={REDACTED}",
        },
    }


def test_redact_text_handles_tokens_without_hiding_normal_operational_text():
    text = "Bearer abc.def-123 failed on /simulate/error with sk-example123456"

    redacted = f"Bearer {REDACTED} failed on /simulate/error with {REDACTED}"
    assert redact_text(text) == redacted
    assert redact_text(redacted) == redacted


def test_log_reader_redacts_parsed_fields_and_raw_lines(tmp_path: Path):
    log_file = tmp_path / "demo-service.log"
    log_file.write_text(
        '{"level":"ERROR","message":"request failed with sk-example123456",'
        '"authorization":"Bearer secret-token","secret":"opaque-value","status_code":500}\n'
        "password=hunter2 could not be parsed\n",
        encoding="utf-8",
    )

    logs = read_recent_logs(log_path=log_file, max_lines=10)
    serialized = json.dumps(logs)

    assert logs[0]["authorization"] == REDACTED
    assert REDACTED in logs[0]["message"]
    assert logs[1]["malformed"] is True
    assert "secret-token" not in serialized
    assert "opaque-value" not in serialized
    assert "sk-example123456" not in serialized
    assert "hunter2" not in serialized


def test_ask_endpoint_redacts_secrets_from_question_and_log_evidence(tmp_path: Path, monkeypatch):
    log_file = tmp_path / "demo-service.log"
    log_file.write_text(
        '{"level":"ERROR","event":"auth_failed","message":"Bearer log-secret failed",'
        '"status_code":500}\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("DEMO_SERVICE_LOG_PATH", str(log_file))

    response = client.post(
        "/ask",
        json={"question": "Why did api_key=question-secret fail?", "use_llm": False},
    )
    serialized = response.text

    assert response.status_code == 200
    assert response.json()["question"] == f"Why did api_key={REDACTED} fail?"
    assert "question-secret" not in serialized
    assert "log-secret" not in serialized


def test_llm_boundary_redacts_every_prompt_input(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "Safe analysis; Bearer provider-secret"}}]}

    class FakeClient:
        def __init__(self, timeout):
            assert timeout == 30

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def post(self, url, headers, json):
            captured["payload"] = json
            return FakeResponse()

    monkeypatch.setattr("app.llm.httpx.Client", FakeClient)
    config = LLMConfig(
        provider="openai",
        api_key="provider-key",
        base_url="https://example.invalid/v1",
        model="test-model",
    )

    result = analyze_with_llm(
        question="Investigate password=question-secret",
        logs=[{"authorization": "Bearer log-secret", "message": "sk-example123456 failed"}],
        rule_based_analysis={"summary": "access_token=analysis-secret"},
        config=config,
    )
    prompt = captured["payload"]["messages"][1]["content"]
    telemetry = json.dumps(result.telemetry)

    assert result.analysis == f"Safe analysis; Bearer {REDACTED}"
    assert result.notice is None
    assert "provider-secret" not in telemetry
    assert "question-secret" not in telemetry
    assert "log-secret" not in telemetry
    assert "analysis-secret" not in telemetry
    assert prompt.count(REDACTED) == 4
    assert "question-secret" not in prompt
    assert "log-secret" not in prompt
    assert "sk-example123456" not in prompt
    assert "analysis-secret" not in prompt
