import json
import os
from dataclasses import dataclass
from typing import Any

import httpx

from app.prompts import ANALYSIS_INSTRUCTIONS, SYSTEM_PROMPT
from app.redaction import redact_data, redact_text


DEFAULT_LLM_MAX_LOG_ENTRIES = 50
DEFAULT_LLM_MAX_PROMPT_CHARS = 12000
TRUNCATION_MARKER = "\n...[truncated by LLM cost controls]\n"


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    api_key: str
    base_url: str
    model: str
    max_log_entries: int = DEFAULT_LLM_MAX_LOG_ENTRIES
    max_prompt_chars: int = DEFAULT_LLM_MAX_PROMPT_CHARS


def load_config() -> LLMConfig:
    provider = os.getenv("LLM_PROVIDER", "none").strip().lower()
    default_base_url = "http://localhost:11434/v1" if provider == "ollama" else "https://api.openai.com/v1"
    return LLMConfig(
        provider=provider,
        api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        base_url=os.getenv("OPENAI_BASE_URL", default_base_url).strip().rstrip("/"),
        model=os.getenv("MODEL_NAME", "gpt-4o-mini").strip(),
        max_log_entries=_read_positive_int("LLM_MAX_LOG_ENTRIES", DEFAULT_LLM_MAX_LOG_ENTRIES),
        max_prompt_chars=_read_positive_int("LLM_MAX_PROMPT_CHARS", DEFAULT_LLM_MAX_PROMPT_CHARS),
    )


def is_configured(config: LLMConfig) -> bool:
    if config.provider in {"", "none", "disabled", "rule-based"}:
        return False
    if config.provider == "ollama":
        return bool(config.base_url and config.model)
    return bool(config.api_key and config.base_url and config.model)


def cost_controls_summary(config: LLMConfig) -> dict[str, int]:
    return {
        "max_log_entries": config.max_log_entries,
        "max_prompt_chars": config.max_prompt_chars,
    }


def analyze_with_llm(
    question: str,
    logs: list[dict[str, Any]],
    rule_based_analysis: dict[str, Any],
    config: LLMConfig | None = None,
) -> tuple[str | None, str | None]:
    config = config or load_config()
    if not is_configured(config):
        return None, "LLM provider is not configured; using rule-based analysis."

    user_prompt, prompt_was_truncated = build_user_prompt(
        question=question,
        logs=logs,
        rule_based_analysis=rule_based_analysis,
        config=config,
    )
    cost_notice = (
        f"LLM prompt was limited to {config.max_prompt_chars} characters by cost controls."
        if prompt_was_truncated
        else None
    )

    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }

    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(f"{config.base_url}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return redact_text(str(content).strip()), cost_notice
    except Exception as exc:
        failure_notice = f"LLM request failed; using rule-based analysis. Error: {redact_text(str(exc))}"
        if cost_notice:
            failure_notice = f"{cost_notice} {failure_notice}"
        return None, failure_notice


def build_user_prompt(
    question: str,
    logs: list[dict[str, Any]],
    rule_based_analysis: dict[str, Any],
    config: LLMConfig,
) -> tuple[str, bool]:
    safe_question = redact_text(question)
    safe_logs = redact_data(logs[-config.max_log_entries :])
    safe_analysis = redact_data(rule_based_analysis)
    evidence = "\n".join(json.dumps(entry, default=str) for entry in safe_logs)

    prompt_header = f"""
Question:
{safe_question}

Rule-based pre-analysis:
{json.dumps(safe_analysis, indent=2, default=str)}

Recent log evidence:
"""
    prompt_footer = f"""

{ANALYSIS_INSTRUCTIONS}
"""
    evidence_budget = config.max_prompt_chars - len(prompt_header) - len(prompt_footer)
    if evidence_budget < 0:
        prompt, _ = _truncate_text(prompt_header + prompt_footer, config.max_prompt_chars)
        return prompt, True

    bounded_evidence, evidence_was_truncated = _truncate_text(evidence, evidence_budget)
    return prompt_header + bounded_evidence + prompt_footer, evidence_was_truncated


def _read_positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default


def _truncate_text(value: str, max_chars: int) -> tuple[str, bool]:
    if len(value) <= max_chars:
        return value, False
    if max_chars <= 0:
        return "", True
    if max_chars <= len(TRUNCATION_MARKER):
        return value[:max_chars], True
    return value[: max_chars - len(TRUNCATION_MARKER)].rstrip() + TRUNCATION_MARKER, True

