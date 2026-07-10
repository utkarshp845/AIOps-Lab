# Kubernetes Incident Debugging Walkthrough

Week 3 Day 6 connects the Kubernetes lessons into one operational workflow.

The goal is to debug a small, intentional incident by moving through evidence in order:

```text
symptom -> Kubernetes state -> app health -> logs -> metrics -> assistant summary -> next steps
```

This walkthrough uses the existing `demo-service` simulation endpoints. Nothing here requires GPUs, Helm, Ingress, Prometheus, Grafana, or a production cluster.

## What You Are Debugging

The scenario is a small incident in the local kind cluster:

- some requests return HTTP 500.
- some requests are slow.
- memory pressure events are emitted.
- logs and metrics contain evidence.
- the AI SRE Assistant summarizes the incident from those signals.

The point is not to fix a real outage. The point is to practice the shape of Kubernetes debugging without being buried in tools.

## Before You Start

Use the kind walkthrough in `../infra/k8s/README.md` first.

You should have:

- kind cluster running.
- local images loaded into kind.
- Kubernetes manifests applied.
- `demo-service` available through port-forward on `localhost:8000`.
- `ai-sre-assistant` available through port-forward on `localhost:8001`.

Port-forward commands:

```bash
kubectl port-forward svc/demo-service 8000:8000 -n ai-infra-starter-kit
```

```bash
kubectl port-forward svc/ai-sre-assistant 8001:8001 -n ai-infra-starter-kit
```

## Step 1: Create Symptoms

Generate mixed normal and failing traffic:

```bash
python scripts/generate-demo-traffic.py --base-url http://localhost:8000 --iterations 10
```

Trigger a guaranteed error:

```bash
curl "http://localhost:8000/simulate/error?probability=1.0"
```

Trigger high latency:

```bash
curl "http://localhost:8000/simulate/latency?min_ms=1200&max_ms=2500"
```

Trigger a memory pressure signal:

```bash
curl "http://localhost:8000/simulate/memory-pressure?size_mb=16"
```

Add an operator marker to the logs:

```bash
curl "http://localhost:8000/simulate/log-event?event=kubernetes_incident_walkthrough&level=warning"
```

This creates enough evidence for Kubernetes inspection, metrics analysis, and assistant summarization.

## Step 2: Check Kubernetes State First

Start broad:

```bash
kubectl get deployments,pods,svc,endpoints,pvc -n ai-infra-starter-kit
```

Then check recent events:

```bash
kubectl get events -n ai-infra-starter-kit --sort-by=.lastTimestamp
```

What this tells you:

- whether pods are running.
- whether pods are ready.
- whether Services have endpoints.
- whether the shared log PVC is bound.
- whether Kubernetes has emitted scheduling, probe, restart, or volume events.

If Kubernetes looks healthy, keep going. The incident may be inside the app rather than in the cluster runtime.

## Step 3: Check App Health And Readiness

From your laptop:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8001/health
```

What this tells you:

- `demo-service` process is alive.
- `demo-service` considers itself ready.
- `ai-sre-assistant` process is alive.

If `/health` and `/ready` are passing while errors still happen, that usually means this is not a basic pod startup problem. It is more likely endpoint-specific, dependency-like, or application-level behavior.

## Step 4: Inspect Logs

Read recent `demo-service` container logs:

```bash
kubectl logs deployment/demo-service -n ai-infra-starter-kit --tail=100
```

Read assistant logs:

```bash
kubectl logs deployment/ai-sre-assistant -n ai-infra-starter-kit --tail=100
```

Look for evidence such as:

- `simulated_checkout_failure`
- `simulated_latency`
- `simulated_memory_pressure`
- `kubernetes_incident_walkthrough`
- request IDs
- HTTP status codes
- endpoint paths

Logs answer: what happened in specific requests?

## Step 5: Inspect Metrics

Fetch raw metrics:

```bash
curl http://localhost:8000/metrics
```

Ask the assistant to analyze metrics:

```bash
curl -s -X POST http://localhost:8001/analyze/metrics \
  -H "Content-Type: application/json" \
  -d '{}'
```

Metrics answer:

- which endpoints saw traffic.
- how many requests returned each status code.
- whether latency buckets show slow requests.
- whether simulated error, latency, or memory pressure counters increased.

Metrics show shape and volume. Logs show individual events.

## Step 6: Ask The Assistant For An Incident Summary

Ask for a combined summary from logs and metrics:

```bash
curl -s -X POST http://localhost:8001/summarize-incident \
  -H "Content-Type: application/json" \
  -d '{"max_lines":200,"use_llm":false}'
```

Ask a targeted question:

```bash
curl -s -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Is this a latency issue, dependency issue, or application bug?","max_lines":200,"use_llm":false}'
```

The assistant should separate:

- observed facts.
- likely causes.
- safe next debugging steps.

The assistant is not replacing debugging. It is helping summarize evidence you already collected.

## Step 7: Decide What You Know

Use this checklist before jumping to fixes:

| Question | Evidence source |
| --- | --- |
| Are pods running? | `kubectl get pods` |
| Are pods ready? | `kubectl get pods`, `kubectl get endpoints` |
| Did Kubernetes report probe, restart, or volume issues? | `kubectl get events`, `kubectl describe pod` |
| Are app health endpoints passing? | `/health`, `/ready` |
| Which endpoints failed? | logs and request metrics |
| Did latency increase? | latency metrics and latency logs |
| Did memory pressure occur? | memory pressure logs and counters |
| What does the assistant think happened? | `/summarize-incident`, `/ask` |

The right next step depends on which layer has evidence.

## Debugging Map

| Symptom | First checks | Likely interpretation |
| --- | --- | --- |
| Pod not running | `kubectl get pods`, `kubectl describe pod` | Kubernetes scheduling, image, crash, or volume issue. |
| Pod running but not ready | readiness probe, endpoints, `/ready` | App is alive but should not receive traffic yet. |
| Health passes but 500s appear | logs, request metrics, assistant summary | Endpoint-specific failure or dependency-like app behavior. |
| Health passes but latency is high | latency endpoint logs, metrics buckets | App is responding slowly, not necessarily crashing. |
| Assistant has no logs | PVC, log path config, demo-service logs | Shared learning log path may not have data yet. |
| Assistant has no metrics | Service endpoints, ConfigMap metrics URL, `/metrics` | Metrics source may be unreachable or misconfigured. |

## Safe Next Steps

Prefer read-only commands first:

```bash
kubectl get deployments,pods,svc,endpoints,pvc -n ai-infra-starter-kit
kubectl get events -n ai-infra-starter-kit --sort-by=.lastTimestamp
kubectl logs deployment/demo-service -n ai-infra-starter-kit --tail=100
curl http://localhost:8000/metrics
curl -s -X POST http://localhost:8001/summarize-incident -H "Content-Type: application/json" -d '{"max_lines":200,"use_llm":false}'
```

Avoid restarting, deleting, or changing resources before you know which layer is failing.

## What This Teaches

This walkthrough ties the project together:

- Kubernetes shows workload state.
- health and readiness show app serving state.
- logs show specific events.
- metrics show aggregate behavior.
- the AI SRE Assistant summarizes evidence.

That is the AI infrastructure learning loop this project is trying to teach.

## Production-Minded Notes

A production version would replace or extend parts of this local workflow:

- shared file logs would become a real log pipeline.
- raw `curl /metrics` would become Prometheus or managed metrics.
- port-forwarding would become Ingress, service mesh, or internal routing.
- manual checks would become dashboards and alerts.
- assistant summaries would need evaluation, access control, and auditability.

For Day 6, the important habit is evidence order: collect facts before changing the system.
