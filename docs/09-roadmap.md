# Roadmap

This is the canonical technical execution order for AIOps Lab. Weeks 1-4 are the completed learning foundation, Weeks 5-8 are the next measurement cycle, and later infrastructure remains gated by evidence and named operational ownership.

## Week 1 - Local Learning Lab

- Local demo-service.
- AI SRE Assistant.
- Docker Compose.
- Sample logs.
- Basic README.

## Week 2 - Observability Basics

- Metrics improvements.
- Structured logging refinements.
- Request correlation.
- Incident examples.
- Assistant metrics analysis.

## Week 3 - Kubernetes Foundations

- kind-first Kubernetes manifests.
- Operations runbook.
- ConfigMaps and Secrets.
- Health checks and resource limits.
- Incident debugging walkthrough.
- Production next-steps guide.

## Week 4 - Production Readiness

- Security hardening basics.
- Secret handling and redaction rules.
- Cost optimization habits.
- Assistant evaluation basics.
- Production observability upgrade path.
- Optional advanced serving roadmap: vLLM, Triton, Ray, KServe, and GPU scheduling.
- Production-readiness review with local and CI release gates.

## Commercialization Track

The [commercialization roadmap](21-commercialization-roadmap.md) runs alongside the technical weeks: audience first, a design-partner wedge second, and paid tiers third. Completing a local technical week does not bypass its customer-discovery or phase-exit gates.

## Week 5 - Provider Telemetry

- Day 1 - complete: expose a bounded per-call contract for provider/model identity, request latency, token usage, outcome, and deterministic fallback without storing sensitive content.
- Day 2 - complete: add aggregate counters and latency distributions with bounded labels.
- Day 3 - complete: accept explicit deployment-owned pricing inputs and return per-call estimated cost metadata only when prices and token directions are known.
- Join provider usage and cost with evaluation outcomes.
- Calculate cost per successful evaluated analysis.

See [Provider Telemetry Contract](22-provider-telemetry.md) for the Day 1 per-request contract, Day 2 aggregate metrics, privacy boundary, and remaining-week sequence.

**Exit gate:** provider usage, reliability, and cost can be compared with evaluation outcomes without storing prompts, incident evidence, credentials, endpoints, or generated content.

## Week 6 - Evaluation Maturity

- Expand the corpus with sanitized incidents, adversarial inputs, prompt-injection cases, incorrect-confidence cases, and redaction edge cases.
- Version the corpus, assistant configuration, and acceptance thresholds together.
- Produce machine-readable evaluation results in CI.
- Keep privacy and safety as hard release gates.

**Exit gate:** a model, prompt, provider, or code change produces a repeatable regression report and cannot bypass required privacy or safety checks.

## Week 7 - Production Signal Path

- Standardize structured stdout logs and cross-service correlation fields.
- Add an optional OpenTelemetry Collector path after signal contracts are stable.
- Add a small dashboard and one actionable, owned alert.
- Exercise one incident from alert through evidence, assistant analysis, runbook action, and recovery review.

**Exit gate:** the project demonstrates a complete symptom-to-recovery workflow without changing the dependency-light quickstart.

## Week 8 - Provider Versus Private Endpoint Benchmark

- Run the same evaluation corpus against deterministic, managed-provider, and OpenAI-compatible private endpoints.
- Measure quality, latency, token usage, fallbacks, throughput, and cost per successful evaluated analysis.
- Test representative input sizes, concurrency, and burst behavior.
- Record a build-versus-buy decision before adding GPU infrastructure.

**Exit gate:** evidence supports continuing with a provider or starting one bounded private-model experiment.

## Internal Pilot Phase

Begin only after the Week 5-8 measurement loop works and the commercialization roadmap has reached the design-partner phase with named owners.

- Authentication, service identity, and role-based access.
- Managed secrets, rotation, artifact pinning, and supply-chain scanning.
- Ingress, TLS, environment separation, and hardened deployment automation.
- Centralized telemetry, retention policies, audit records, quotas, and budgets.
- Initial SLOs, routed alerts, rollback tests, and recovery exercises.
- Private evaluation datasets and controlled evidence access.

**Exit gate:** a sanitized internal pilot can operate with explicit ownership, access controls, measurable reliability, and a tested rollback path.

## Advanced Serving Phase - Only If Earned

- Test one approved model behind an authenticated OpenAI-compatible endpoint.
- Add an optional single-GPU vLLM example only when the Week 8 benchmark or a named deployment requirement justifies it.
- Add GPU scheduling, quotas, utilization telemetry, queue metrics, and out-of-memory recovery tests for a real workload.
- Introduce Ray Serve, Triton, or KServe only when its specific orchestration problem appears.
- Consider enterprise VPC, dedicated, or on-premises packaging after customer demand is validated.

The default project remains deterministic, provider-compatible, laptop-friendly, and GPU-free throughout these phases.

## Longer-Term Product Backlog

- Hosted evaluation history and regression alerts.
- Team collaboration and private incident datasets.
- Audit-ready exports, policy controls, and usage governance.
- Privacy-aware product outcome telemetry.
- Provider and model quality/cost comparisons over time.
- Log, metrics, and trace backend examples using Prometheus, Grafana, compatible open-source components, or managed services.
- Multi-environment and cloud deployment examples.
- Horizontal Pod Autoscaling for measured non-GPU workloads.
