# Kubernetes Production Next Steps

Week 3 Day 7 closes the first Kubernetes chapter of `ai-infra-starter-kit`.

The local kind setup now teaches the core mapping:

```text
Docker Compose learning lab
  -> Kubernetes namespace
  -> Deployments and Pods
  -> Services
  -> ConfigMaps and Secrets
  -> PVC-backed shared logs for local learning
  -> readiness and liveness probes
  -> resource requests and limits
  -> incident debugging workflow
```

The goal of Week 3 was not to make the repo production-grade. The goal was to make Kubernetes understandable without losing the production direction.

## What Week 3 Proved

The same system can run in Kubernetes while keeping the original mental model:

```text
demo-service -> logs/metrics -> ai-sre-assistant -> operational summary
```

Kubernetes changed the runtime, not the learning loop.

What now works locally:

- `demo-service` runs as a Deployment.
- `ai-sre-assistant` runs as a Deployment.
- Services provide stable in-cluster networking.
- ConfigMap values configure log paths, metrics URLs, provider settings, and model names.
- Secret wiring allows an optional `OPENAI_API_KEY` without requiring one.
- A local shared volume keeps the log-reading lesson working in kind.
- Probes and resource settings introduce real Kubernetes operating behavior.
- The incident walkthrough connects Kubernetes state, app health, logs, metrics, and assistant analysis.

## What Is Still Local-Only

These choices are intentional learning defaults, not production recommendations.

| Local choice | Why it exists now | What production would use |
| --- | --- | --- |
| kind cluster | Fast local Kubernetes learning | managed Kubernetes or a real cluster |
| one replica per app | Avoid shared-volume confusion | multiple replicas with stateless app design |
| shared PVC for logs | Keeps the assistant log-reading path simple | log collector and centralized log backend |
| ClusterIP plus port-forward | Works on a laptop | Ingress, gateway, load balancer, or internal routing |
| simple Kubernetes Secret | Teaches the primitive | external secret manager or encrypted secrets workflow |
| static requests and limits | Gives a safe starting point | tuned values based on real metrics |
| manual curl checks | Keeps the workflow visible | dashboards, alerts, and SLOs |
| rule-based assistant fallback | Works without API keys | evaluated assistant behavior with access control and audit logs |

The repo should keep these tradeoffs explicit. Beginner-friendly does not mean pretending local shortcuts are production architecture.

## Production Upgrade Path

A production-minded path from here should happen in layers.

### 1. Logging Pipeline

Replace shared file logs with a real collection path:

```text
app stdout -> collector/agent -> log backend -> assistant/query layer
```

Options later could include OpenTelemetry Collector, Fluent Bit, Loki, Elasticsearch, CloudWatch, or a managed observability platform.

The important shift is that app pods should not share a writable log file in production.

### 2. Metrics And Dashboards

The repo already exposes Prometheus-style metrics.

Next production step:

```text
demo-service /metrics -> Prometheus or managed metrics -> dashboard/alerts
```

Week 4 can introduce what to measure before introducing a full stack:

- request rate.
- error rate.
- latency buckets.
- pod restarts.
- resource usage.
- assistant analysis usage.

### 3. Ingress And Traffic

Port-forwarding is a learning tool.

Production needs a real traffic path:

- Ingress or Gateway API.
- TLS.
- hostnames.
- request timeouts.
- authentication where needed.
- clear public vs private service boundaries.

This should come after the internal service model is clear.

### 4. Secrets And Configuration

Kubernetes Secrets are the first concept, not the final answer.

Production should consider:

- external secret managers.
- secret rotation.
- RBAC around who can read secrets.
- encrypted secret workflows.
- environment-specific config.
- audit trails.

The current `secret.example.yaml` is documentation only.

### 5. Scaling And Availability

This repo intentionally uses one replica today.

Production questions to answer later:

- Can the service run multiple replicas safely?
- Where do logs go if there is no shared file?
- Which state must move out of the pod?
- What request and memory patterns should inform resource values?
- What metrics should drive autoscaling?

Autoscaling should come after requests, limits, and service behavior are understood.

### 6. AI Assistant Safety

An AI SRE Assistant needs more than an LLM call in production.

Production concerns include:

- evidence grounding.
- prompt injection resistance.
- data access boundaries.
- redaction of secrets and sensitive logs.
- evaluation sets for incident summaries.
- human review for high-impact recommendations.
- audit logs for assistant usage.

The current assistant is intentionally conservative and falls back to deterministic analysis.

## Week 4 Direction

Week 4 should move from local Kubernetes basics into production readiness thinking.

Recommended sequence:

1. Security hardening basics.
2. Secret handling and redaction rules.
3. Cost optimization habits.
4. Assistant evaluation basics.
5. Production observability upgrade path.
6. Optional advanced serving roadmap: vLLM, Triton, Ray, KServe, and GPU scheduling.

The key is to keep the project anchored in the working lab. Each advanced tool should answer a specific problem the lab has already revealed.

## Week 3 Takeaway

I did not learn Kubernetes by adding every Kubernetes tool.

I learned how this app maps into Kubernetes:

- Deployment.
- Pod.
- Service.
- ConfigMap.
- Secret.
- PVC.
- probes.
- resources.
- logs.
- metrics.
- incident workflow.

That is enough foundation to start asking better production questions.
