# Incident: Latency Spike

## Symptom

The service is responding more slowly than expected.

An operator might notice:

- Slow API calls.
- Latency bucket counts increasing.
- WARNING logs with `event="simulated_latency"`.
- `request_completed` logs with high `duration_ms`.

## Reproduce Locally

Start the stack:

```bash
make up
```

No `make` installed:

```bash
docker compose up --build -d
```

Trigger slow traffic:

```bash
curl -i -H "X-Request-ID: incident-latency-001" "http://localhost:8000/simulate/latency?min_ms=1200&max_ms=1600"
```

Analyze recent logs:

```bash
make analyze-logs
```

No `make` installed:

```bash
docker compose run --rm --no-deps ai-sre-assistant python cli/sre.py ask "Is this a latency issue?" --max-lines 120
```

## Metrics Evidence

Check:

```bash
curl http://localhost:8000/metrics
```

Useful metrics:

```text
demo_service_http_request_duration_seconds_bucket{method="GET",path="/simulate/latency",le="1"}
demo_service_http_request_duration_seconds_bucket{method="GET",path="/simulate/latency",le="2.5"}
demo_service_simulated_latency_events_total{endpoint="/simulate/latency"}
```

What this tells us:

- The latency is tied to `/simulate/latency`.
- Buckets show whether requests are crossing useful thresholds.
- The simulation counter confirms intentional latency events occurred.

## Log Evidence

Look for logs with the same request ID:

```text
event="simulated_latency" latency_ms=1400 request_id="incident-latency-001"
event="request_completed" duration_ms=1405 status_code=200 request_id="incident-latency-001"
```

What this tells us:

- The route intentionally slept before responding.
- The final request duration matches the simulated latency.
- The response can be slow even when the status code is 200.

## Likely Cause

This is an intentional latency simulation from `/simulate/latency`.

The likely cause is test traffic or demo traffic using high `min_ms` and `max_ms` values.

## Safe Debugging Steps

- Confirm whether slow requests are isolated to `/simulate/latency`.
- Compare normal API paths like `/api/orders` against the latency endpoint.
- Check whether slow requests still return 200 responses.
- Use the request ID to connect the latency event and final request log.
- Avoid treating this as a system-wide outage unless normal endpoints are also slow.

## What The AI SRE Assistant Should Say

The assistant should say:

- Facts: recent logs show slow events and high request duration.
- Evidence: the slow endpoint is `/simulate/latency`.
- Likely cause: intentional latency simulation.
- Next step: compare latency metrics for normal endpoints versus simulation endpoints.
- Confidence: high if logs include `event="simulated_latency"` and matching `request_completed` duration.

