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

## Structured Logs And Request Correlation

Metrics show the shape of a problem. Logs explain the story behind specific events.

For logs to be useful during an incident, related events need a shared field. `demo-service` uses `request_id` for that.

The service now:

- Accepts an incoming `X-Request-ID` header.
- Generates a request ID when the caller does not provide one.
- Returns the request ID in the `x-request-id` response header.
- Adds the same request ID to route-level logs and the final `request_completed` log.

This lets one request become a traceable sequence:

```text
simulated_error request_id=demo-request-123
request_completed request_id=demo-request-123 status_code=500
```

Useful structured log fields:

- `timestamp`: when the event happened.
- `level`: log severity such as `INFO`, `WARNING`, or `ERROR`.
- `service`: which service emitted the log.
- `event`: stable machine-readable event name.
- `message`: human-readable summary.
- `method`: HTTP method for request logs.
- `path`: normalized route path when available.
- `endpoint`: source endpoint for route-level events.
- `status_code`: HTTP response status.
- `duration_ms`: request duration.
- `request_id`: correlation ID for following one request through logs.
- `error_type`: stable error category when a failure is known.

The goal is not to log everything. The goal is to log enough consistent evidence that a human or AI assistant can separate facts from guesses.

## Incident Walkthroughs

The next step is using logs and metrics together.

Start with:

- [Error spike](incidents/01-error-spike.md)
- [Latency spike](incidents/02-latency-spike.md)
- [Memory pressure](incidents/03-memory-pressure.md)

Each walkthrough follows the same operator pattern:

```text
Symptom -> Metrics evidence -> Log evidence -> Likely cause -> Safe next steps
```

That pattern is also the intended behavior for the AI SRE Assistant.

## Production Upgrade Path

The local shared-log and direct-metrics workflow is a teaching bridge. For centralized collection, backends, dashboards, SLOs, alerts, assistant telemetry, and privacy-aware product signals, continue with [Production Observability Upgrade Path](18-production-observability.md).
