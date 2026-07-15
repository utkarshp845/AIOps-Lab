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


def test_llm_prompt_respects_prompt_character_budget(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "bounded analysis"}}]}

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
    config = LLMConfig(
        provider="openai",
        api_key="provider-key",
        base_url="https://example.invalid/v1",
        model="test-model",
        max_log_entries=5,
        max_prompt_chars=350,
    )

    result, notice = analyze_with_llm(
        question="Investigate the latest failure",
        logs=[{"message": "x" * 2000}],
        rule_based_analysis={"summary": "y" * 1000},
        config=config,
    )

    assert result == "bounded analysis"
    assert notice == "LLM prompt was limited to 350 characters by cost controls."
    assert len(captured["prompt"]) <= 350


def test_api_response_reports_llm_cost_controls(tmp_path, monkeypatch):
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
    assert "LLM provider is not configured" in body["llm_notice"]
