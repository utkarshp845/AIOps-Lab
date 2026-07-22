import json
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.prompts import ANALYSIS_INSTRUCTIONS, SYSTEM_PROMPT
from app.provider_metrics import PROVIDER_METRICS
from app.redaction import redact_data, redact_text


DEFAULT_LLM_MAX_LOG_ENTRIES = 50
DEFAULT_LLM_MAX_PROMPT_CHARS = 12000
TRUNCATION_MARKER = "\n...[truncated by LLM cost controls]\n"
MAX_TELEMETRY_LABEL_CHARS = 100


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    api_key: str
    base_url: str
    model: str
    max_log_entries: int = DEFAULT_LLM_MAX_LOG_ENTRIES
    max_prompt_chars: int = DEFAULT_LLM_MAX_PROMPT_CHARS


@dataclass(frozen=True)
class LLMCallResult:
    analysis: str | None
    notice: str | None
    telemetry: dict[str, Any]


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
) -> LLMCallResult:
    config = config or load_config()
    if not is_configured(config):
        return LLMCallResult(
            analysis=None,
            notice="LLM provider is not configured; using rule-based analysis.",
            telemetry=_telemetry(
                config=config,
                configured=False,
                attempted=False,
                outcome="not_configured",
                fallback_used=True,
                fallback_reason="provider_not_configured",
            ),
        )

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

    request_started = time.perf_counter()
    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(f"{config.base_url}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            analysis = redact_text(str(content).strip())
            if not analysis:
                raise ValueError("LLM response content was empty")
            return LLMCallResult(
                analysis=analysis,
                notice=cost_notice,
                telemetry=_telemetry(
                    config=config,
                    configured=True,
                    attempted=True,
                    outcome="success",
                    fallback_used=False,
                    fallback_reason=None,
                    request_latency_ms=_elapsed_ms(request_started),
                    usage=data.get("usage"),
                ),
            )
    except Exception as exc:
        failure_notice = f"LLM request failed; using rule-based analysis. Error: {redact_text(str(exc))}"
        if cost_notice:
            failure_notice = f"{cost_notice} {failure_notice}"
        return LLMCallResult(
            analysis=None,
            notice=failure_notice,
            telemetry=_telemetry(
                config=config,
                configured=True,
                attempted=True,
                outcome="failure",
                fallback_used=True,
                fallback_reason="provider_request_failed",
                request_latency_ms=_elapsed_ms(request_started),
            ),
        )


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


def _telemetry(
    config: LLMConfig,
    *,
    configured: bool,
    attempted: bool,
    outcome: str,
    fallback_used: bool,
    fallback_reason: str | None,
    request_latency_ms: float | None = None,
    usage: Any = None,
) -> dict[str, Any]:
    telemetry = {
        "provider": _bounded_label(config.provider or "none"),
        "model": _bounded_label(config.model) if configured else None,
        "configured": configured,
        "attempted": attempted,
        "outcome": outcome,
        "request_latency_ms": request_latency_ms,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "usage": _normalize_usage(usage),
    }
    PROVIDER_METRICS.observe(telemetry)
    return telemetry


def _normalize_usage(usage: Any) -> dict[str, int | bool | None]:
    if not isinstance(usage, dict):
        usage = {}

    input_tokens = _non_negative_int(usage.get("prompt_tokens"))
    output_tokens = _non_negative_int(usage.get("completion_tokens"))
    total_tokens = _non_negative_int(usage.get("total_tokens"))
    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens

    return {
        "reported": any(value is not None for value in (input_tokens, output_tokens, total_tokens)),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def _non_negative_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _bounded_label(value: str) -> str:
    return redact_text(str(value).strip())[:MAX_TELEMETRY_LABEL_CHARS]


def _elapsed_ms(started: float) -> float:
    return round(max(0.0, (time.perf_counter() - started) * 1000), 2)

