# Observability Basics

Observability starts with three questions:

- Is the service up?
- Is it doing the right work?
- When it fails, can we see enough evidence to debug it?

## Day 1 Signals

`demo-service` emits:

- Health via `/health`.
- Readiness via `/ready`.
- Structured logs for every request.
- Error logs for simulated failures.
- Warning logs for latency and memory pressure.
- Prometheus-style metrics via `/metrics`.

## What To Look For

- HTTP 5xx counts.
- Slow request durations.
- Repeated warning events.
- Missing or malformed structured fields.
- Differences between normal API paths and simulation paths.

The AI assistant is only useful when these signals are clear.

## Metrics Cleanup

Week 2 starts by making metrics stable and teachable.

`demo-service` exposes counters and latency buckets:

- `demo_service_http_requests_total`
- `demo_service_http_request_duration_seconds_bucket`
- `demo_service_http_request_duration_seconds_sum`
- `demo_service_http_request_duration_seconds_count`
- `demo_service_simulated_errors_total`
- `demo_service_simulated_latency_events_total`
- `demo_service_memory_pressure_events_total`

Counters answer "how many times did this happen?"

Latency buckets answer "how often did requests finish under useful thresholds?"

## Label Cardinality

Metrics labels should stay low-cardinality. This means labels should not contain unbounded values such as request IDs, user IDs, or order IDs.

Bad:

```text
path="/api/orders/ord-1001"
path="/api/orders/ord-1002"
path="/api/orders/ord-1003"
```

Better:

```text
path="/api/orders/{order_id}"
```

The cleaned-up metrics use FastAPI route templates where possible so dynamic IDs do not explode the number of time series.
