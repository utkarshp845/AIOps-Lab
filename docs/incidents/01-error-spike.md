# Incident: Error Spike

## Symptom

The service starts returning HTTP 500 responses.

An operator might notice:

- API calls failing.
- `demo_service_http_requests_total` increasing with `status_code="500"`.
- `demo_service_simulated_errors_total` increasing.
- ERROR logs with `event="simulated_error"`.

## Reproduce Locally

Start the stack:

```bash
make up
```

No `make` installed:

```bash
docker compose up --build -d
```

Trigger a known failure:

```bash
curl -i -H "X-Request-ID: incident-error-001" "http://localhost:8000/simulate/error?probability=1.0"
```

Analyze recent logs:

```bash
make analyze-logs
```

No `make` installed:

```bash
docker compose run --rm --no-deps ai-sre-assistant python cli/sre.py ask "Why is the demo service failing?" --max-lines 120
```

## Metrics Evidence

Check:

```bash
curl http://localhost:8000/metrics
```

Useful metrics:

```text
demo_service_http_requests_total{method="GET",path="/simulate/error",status_code="500"}
demo_service_simulated_errors_total{endpoint="/simulate/error",error_type="checkout_dependency_timeout"}
```

What this tells us:

- HTTP 500s are happening.
- The failures are tied to the intentional `/simulate/error` endpoint.
- The stable `error_type` is `checkout_dependency_timeout`.

## Log Evidence

Look for logs with the same request ID:

```text
event="simulated_error" request_id="incident-error-001"
event="request_completed" status_code=500 request_id="incident-error-001"
```

What this tells us:

- The route emitted an ERROR event.
- The final request log confirms the response status was 500.
- The shared request ID connects both log lines.

## Likely Cause

This is an intentional simulated dependency timeout from `/simulate/error`.

The most likely cause is test traffic hitting the simulation endpoint, not a real production dependency outage.

## Safe Debugging Steps

- Confirm the failing path is `/simulate/error`.
- Check whether recent traffic intentionally called the simulation endpoint.
- Compare the 500 count against normal API paths like `/api/orders`.
- Use the request ID to inspect related log lines.
- Avoid changing infrastructure until the evidence points outside the app.

## What The AI SRE Assistant Should Say

The assistant should say:

- Facts: recent logs show ERROR events and HTTP 500 responses.
- Evidence: the failing endpoint is `/simulate/error`.
- Likely cause: intentional simulated checkout dependency timeout.
- Next step: confirm whether generated traffic or a manual test triggered the endpoint.
- Confidence: high if the error logs include `event="simulated_error"` and `error_type="checkout_dependency_timeout"`.

