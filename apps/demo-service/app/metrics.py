from collections import Counter, defaultdict
from threading import Lock


LATENCY_BUCKETS_SECONDS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf"))


class MetricsRegistry:
    """Tiny in-memory metrics registry for teaching Prometheus basics without extra dependencies."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._http_requests: Counter[tuple[str, str, str]] = Counter()
        self._http_duration_buckets: Counter[tuple[str, str, float]] = Counter()
        self._http_duration_count: Counter[tuple[str, str]] = Counter()
        self._http_duration_sum: defaultdict[tuple[str, str], float] = defaultdict(float)
        self._simulated_errors: Counter[tuple[str, str]] = Counter()
        self._simulated_latency_events: Counter[str] = Counter()
        self._memory_pressure_events: Counter[str] = Counter()

    def reset(self) -> None:
        with self._lock:
            self._http_requests.clear()
            self._http_duration_buckets.clear()
            self._http_duration_count.clear()
            self._http_duration_sum.clear()
            self._simulated_errors.clear()
            self._simulated_latency_events.clear()
            self._memory_pressure_events.clear()

    def observe_http_request(self, method: str, path: str, status_code: int, duration_seconds: float) -> None:
        method = method.upper()
        status = str(status_code)

        with self._lock:
            self._http_requests[(method, path, status)] += 1
            self._http_duration_count[(method, path)] += 1
            self._http_duration_sum[(method, path)] += duration_seconds

            for bucket in LATENCY_BUCKETS_SECONDS:
                if duration_seconds <= bucket:
                    self._http_duration_buckets[(method, path, bucket)] += 1

    def record_simulated_error(self, endpoint: str, error_type: str) -> None:
        with self._lock:
            self._simulated_errors[(endpoint, error_type)] += 1

    def record_simulated_latency(self, endpoint: str) -> None:
        with self._lock:
            self._simulated_latency_events[endpoint] += 1

    def record_memory_pressure(self, endpoint: str) -> None:
        with self._lock:
            self._memory_pressure_events[endpoint] += 1

    def render_prometheus(self) -> str:
        with self._lock:
            http_requests = self._http_requests.copy()
            duration_buckets = self._http_duration_buckets.copy()
            duration_count = self._http_duration_count.copy()
            duration_sum = dict(self._http_duration_sum)
            simulated_errors = self._simulated_errors.copy()
            simulated_latency_events = self._simulated_latency_events.copy()
            memory_pressure_events = self._memory_pressure_events.copy()

        lines = [
            "# HELP demo_service_http_requests_total Total HTTP requests handled by demo-service.",
            "# TYPE demo_service_http_requests_total counter",
        ]
        for (method, path, status_code), count in sorted(http_requests.items()):
            labels = _labels(method=method, path=path, status_code=status_code)
            lines.append(f"demo_service_http_requests_total{{{labels}}} {count}")

        lines.extend(
            [
                "# HELP demo_service_http_request_duration_seconds HTTP request duration in seconds.",
                "# TYPE demo_service_http_request_duration_seconds histogram",
            ]
        )
        for method, path in sorted(duration_count):
            for bucket in LATENCY_BUCKETS_SECONDS:
                labels = _labels(method=method, path=path, le=_format_bucket(bucket))
                count = duration_buckets[(method, path, bucket)]
                lines.append(f"demo_service_http_request_duration_seconds_bucket{{{labels}}} {count}")

            base_labels = _labels(method=method, path=path)
            lines.append(
                f"demo_service_http_request_duration_seconds_sum{{{base_labels}}} {duration_sum[(method, path)]:.6f}"
            )
            lines.append(f"demo_service_http_request_duration_seconds_count{{{base_labels}}} {duration_count[(method, path)]}")

        lines.extend(
            [
                "# HELP demo_service_simulated_errors_total Intentional simulated errors by endpoint and error type.",
                "# TYPE demo_service_simulated_errors_total counter",
            ]
        )
        for (endpoint, error_type), count in sorted(simulated_errors.items()):
            labels = _labels(endpoint=endpoint, error_type=error_type)
            lines.append(f"demo_service_simulated_errors_total{{{labels}}} {count}")

        lines.extend(
            [
                "# HELP demo_service_simulated_latency_events_total Intentional latency simulation events by endpoint.",
                "# TYPE demo_service_simulated_latency_events_total counter",
            ]
        )
        for endpoint, count in sorted(simulated_latency_events.items()):
            lines.append(f"demo_service_simulated_latency_events_total{{{_labels(endpoint=endpoint)}}} {count}")

        lines.extend(
            [
                "# HELP demo_service_memory_pressure_events_total Intentional memory pressure simulation events.",
                "# TYPE demo_service_memory_pressure_events_total counter",
            ]
        )
        for endpoint, count in sorted(memory_pressure_events.items()):
            lines.append(f"demo_service_memory_pressure_events_total{{{_labels(endpoint=endpoint)}}} {count}")

        return "\n".join(lines) + "\n"


def _format_bucket(bucket: float) -> str:
    if bucket == float("inf"):
        return "+Inf"
    return f"{bucket:g}"


def _labels(**labels: str) -> str:
    return ",".join(f'{key}="{_escape_label(value)}"' for key, value in labels.items())


def _escape_label(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


METRICS = MetricsRegistry()

