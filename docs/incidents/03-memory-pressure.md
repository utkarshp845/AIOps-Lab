# Incident: Memory Pressure

## Symptom

The service emits warnings about memory pressure.

An operator might notice:

- WARNING logs with `event="simulated_memory_pressure"`.
- `demo_service_memory_pressure_events_total` increasing.
- Requests to `/simulate/memory-pressure`.

## Reproduce Locally

Start the stack:

```bash
make up
```

No `make` installed:

```bash
docker compose up --build -d
```

Trigger memory pressure:

```bash
curl -i -H "X-Request-ID: incident-memory-001" "http://localhost:8000/simulate/memory-pressure?size_mb=16"
```

Analyze recent logs:

```bash
make analyze-logs
```

No `make` installed:

```bash
docker compose run --rm --no-deps ai-sre-assistant python cli/sre.py ask "Are there signs of memory pressure?" --max-lines 120
```

## Metrics Evidence

Check:

```bash
curl http://localhost:8000/metrics
```

Useful metric:

```text
demo_service_memory_pressure_events_total{endpoint="/simulate/memory-pressure"}
```

What this tells us:

- The memory pressure endpoint was called.
- The event count is increasing when memory pressure is simulated.

## Log Evidence

Look for logs with the same request ID:

```text
event="simulated_memory_pressure" memory_mb=16 request_id="incident-memory-001"
event="request_completed" path="/simulate/memory-pressure" status_code=200 request_id="incident-memory-001"
```

What this tells us:

- The service intentionally allocated memory during the request.
- The request completed successfully.
- The warning is useful operational evidence, not necessarily a crash.

## Likely Cause

This is intentional memory pressure from `/simulate/memory-pressure`.

The likely cause is generated demo traffic or a manual simulation request.

## Safe Debugging Steps

- Confirm the requested `size_mb` value.
- Check whether memory warnings line up with calls to `/simulate/memory-pressure`.
- Keep local memory pressure values small.
- Add resource limits before using this pattern in Kubernetes demos.
- Do not assume a memory leak unless memory remains high after requests complete.

## What The AI SRE Assistant Should Say

The assistant should say:

- Facts: recent logs show memory pressure warnings.
- Evidence: the endpoint is `/simulate/memory-pressure`.
- Likely cause: intentional simulation.
- Next step: confirm requested memory size and whether warnings line up with demo traffic.
- Confidence: medium to high if logs include `event="simulated_memory_pressure"` and matching request IDs.

