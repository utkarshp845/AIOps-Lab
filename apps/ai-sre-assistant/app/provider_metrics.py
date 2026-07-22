from collections import Counter, defaultdict
from math import isfinite
from threading import Lock
from typing import Any

from app.redaction import redact_text


PROVIDER_LATENCY_BUCKETS_SECONDS = (
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
    30.0,
    float("inf"),
)
MAX_METRIC_LABEL_CHARS = 100
VALID_OUTCOMES = {"success", "failure", "not_configured"}
VALID_FALLBACK_REASONS = {"provider_not_configured", "provider_request_failed"}


class ProviderMetricsRegistry:
    """Small in-memory provider registry with a fixed, privacy-safe label contract."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._analyses: Counter[tuple[str, str, str]] = Counter()
        self._latency_buckets: Counter[tuple[str, str, str, float]] = Counter()
        self._latency_count: Counter[tuple[str, str, str]] = Counter()
        self._latency_sum: defaultdict[tuple[str, str, str], float] = defaultdict(float)
        self._fallbacks: Counter[tuple[str, str, str]] = Counter()
        self._tokens: Counter[tuple[str, str, str]] = Counter()

    def reset(self) -> None:
        with self._lock:
            self._analyses.clear()
            self._latency_buckets.clear()
            self._latency_count.clear()
            self._latency_sum.clear()
            self._fallbacks.clear()
            self._tokens.clear()

    def observe(self, telemetry: dict[str, Any]) -> None:
        provider = _bounded_label(telemetry.get("provider"), default="unknown")
        model = _bounded_label(telemetry.get("model"), default="none")
        outcome = telemetry.get("outcome")
        outcome = outcome if outcome in VALID_OUTCOMES else "unknown"

        with self._lock:
            self._analyses[(provider, model, outcome)] += 1

            latency_seconds = _latency_seconds(telemetry)
            if latency_seconds is not None:
                latency_key = (provider, model, outcome)
                self._latency_count[latency_key] += 1
                self._latency_sum[latency_key] += latency_seconds
                for bucket in PROVIDER_LATENCY_BUCKETS_SECONDS:
                    if latency_seconds <= bucket:
                        self._latency_buckets[(*latency_key, bucket)] += 1

            fallback_reason = telemetry.get("fallback_reason")
            if telemetry.get("fallback_used") is True:
                reason = (
                    fallback_reason
                    if fallback_reason in VALID_FALLBACK_REASONS
                    else "other"
                )
                self._fallbacks[(provider, model, reason)] += 1

            usage = telemetry.get("usage")
            if isinstance(usage, dict):
                for direction, field in (
                    ("input", "input_tokens"),
                    ("output", "output_tokens"),
                ):
                    value = usage.get(field)
                    if (
                        isinstance(value, int)
                        and not isinstance(value, bool)
                        and value >= 0
                    ):
                        self._tokens[(provider, model, direction)] += value

    def render_prometheus(self) -> str:
        with self._lock:
            analyses = self._analyses.copy()
            latency_buckets = self._latency_buckets.copy()
            latency_count = self._latency_count.copy()
            latency_sum = dict(self._latency_sum)
            fallbacks = self._fallbacks.copy()
            tokens = self._tokens.copy()

        lines = [
            "# HELP ai_sre_provider_analyses_total LLM enrichment selections by provider, model, and outcome.",
            "# TYPE ai_sre_provider_analyses_total counter",
        ]
        for (provider, model, outcome), count in sorted(analyses.items()):
            labels = _labels(provider=provider, model=model, outcome=outcome)
            lines.append(f"ai_sre_provider_analyses_total{{{labels}}} {count}")

        lines.extend(
            [
                "# HELP ai_sre_provider_request_duration_seconds Attempted provider request duration in seconds.",
                "# TYPE ai_sre_provider_request_duration_seconds histogram",
            ]
        )
        for provider, model, outcome in sorted(latency_count):
            for bucket in PROVIDER_LATENCY_BUCKETS_SECONDS:
                labels = _labels(
                    provider=provider,
                    model=model,
                    outcome=outcome,
                    le=_format_bucket(bucket),
                )
                count = latency_buckets[(provider, model, outcome, bucket)]
                lines.append(
                    f"ai_sre_provider_request_duration_seconds_bucket{{{labels}}} {count}"
                )

            base_labels = _labels(provider=provider, model=model, outcome=outcome)
            lines.append(
                f"ai_sre_provider_request_duration_seconds_sum{{{base_labels}}} "
                f"{latency_sum[(provider, model, outcome)]:.6f}"
            )
            lines.append(
                f"ai_sre_provider_request_duration_seconds_count{{{base_labels}}} "
                f"{latency_count[(provider, model, outcome)]}"
            )

        lines.extend(
            [
                "# HELP ai_sre_provider_fallbacks_total Deterministic provider fallbacks by bounded reason.",
                "# TYPE ai_sre_provider_fallbacks_total counter",
            ]
        )
        for (provider, model, reason), count in sorted(fallbacks.items()):
            labels = _labels(provider=provider, model=model, reason=reason)
            lines.append(f"ai_sre_provider_fallbacks_total{{{labels}}} {count}")

        lines.extend(
            [
                "# HELP ai_sre_provider_tokens_total Provider-reported tokens by input or output direction.",
                "# TYPE ai_sre_provider_tokens_total counter",
            ]
        )
        for (provider, model, direction), count in sorted(tokens.items()):
            labels = _labels(provider=provider, model=model, direction=direction)
            lines.append(f"ai_sre_provider_tokens_total{{{labels}}} {count}")

        return "\n".join(lines) + "\n"


def _latency_seconds(telemetry: dict[str, Any]) -> float | None:
    if telemetry.get("attempted") is not True:
        return None
    latency_ms = telemetry.get("request_latency_ms")
    if not isinstance(latency_ms, (int, float)) or isinstance(latency_ms, bool):
        return None
    if not isfinite(latency_ms) or latency_ms < 0:
        return None
    return latency_ms / 1000


def _bounded_label(value: Any, *, default: str) -> str:
    if value is None:
        return default
    label = redact_text(str(value).strip())[:MAX_METRIC_LABEL_CHARS]
    return label or default


def _format_bucket(bucket: float) -> str:
    if bucket == float("inf"):
        return "+Inf"
    return f"{bucket:g}"


def _labels(**labels: str) -> str:
    return ",".join(f'{key}="{_escape_label(value)}"' for key, value in labels.items())


def _escape_label(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


PROVIDER_METRICS = ProviderMetricsRegistry()
