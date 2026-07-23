# Production Considerations

Day 1 is local and simple. Production adds constraints.

This repo uses a gradual path on purpose:

```text
local app -> AI service -> logs/metrics -> assistant -> containers -> Kubernetes -> production considerations
```

The goal is not to hide production complexity. The goal is to introduce it in the right order.

## Logging

A shared file is useful locally because it makes the assistant workflow easy to see.

Production should use a real log pipeline:

```text
app stdout -> collector/agent -> log backend -> query/assistant layer
```

Options include OpenTelemetry Collector, Fluent Bit, Loki, Elasticsearch, CloudWatch, or a managed observability platform.

## Metrics And Observability

The demo service exposes Prometheus-style metrics so the project can teach counters, latency buckets, and error patterns before adding a full observability stack.

Production should add:

- metrics scraping or managed metrics ingestion.
- dashboards for rate, errors, latency, saturation, and restarts.
- alert thresholds tied to symptoms users care about.
- incident examples that connect metrics to logs and assistant output.

See [Production Observability Upgrade Path](18-production-observability.md) for a staged architecture, signal ownership, SLO and alert guidance, assistant quality metrics, and product-value measurement.

## Health And Readiness

Health checks should answer whether the process is alive.

Readiness checks should answer whether the service can safely receive traffic.

Bad liveness probes can make incidents worse by restarting an app that is slow but recovering.

## Configuration And Secrets

ConfigMaps are fine for normal configuration.

Secrets should hold sensitive values, but Kubernetes Secrets are only the first primitive. Production should consider external secret managers, rotation, RBAC, encryption workflows, and auditability.

Never commit real API keys.

## Reliability

Before adding advanced model serving, define:

- SLOs.
- Error budgets.
- Alert thresholds.
- Rollback paths.
- Incident review habits.
- Safe operational commands.

## Scaling

The local Kubernetes setup uses one replica to keep the shared-log learning model simple.

Production scaling requires a different design:

- stateless app replicas.
- centralized logs.
- resource values based on observed usage.
- autoscaling signals chosen from real metrics.
- rollout strategy and rollback checks.

## AI Assistant Safety

An AI SRE Assistant should be evidence-grounded and conservative.

Production concerns include:

- access control.
- redaction of secrets and sensitive data.
- prompt injection resistance.
- audit logs.
- evaluation sets for incident summaries.
- human review for risky recommendations.

The assistant should not pretend to know things that are not present in logs, metrics, or provided context.

## Advanced Serving Comes Later

Tools such as vLLM, Triton, Ray, KServe, and GPU scheduling are valuable when the project reaches model serving scale.

They are roadmap items, not Day 1 requirements.

Before adding them, the repo should already explain the operational foundation: logs, metrics, health checks, Kubernetes basics, security, cost, and evaluation.

See [Advanced Model Serving Roadmap](19-advanced-model-serving-roadmap.md) for adoption gates, framework boundaries, benchmark criteria, GPU operating requirements, and operational tradeoffs.
