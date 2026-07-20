# Production Readiness Review

Week 4, Day 7 closes the first AIOps Lab learning cycle with an explicit release decision.

The project now demonstrates a complete local path from application signals to evidence-grounded incident analysis. That makes it ready to publish as a learning lab. It does not make the current Docker Compose or kind configuration ready for internet-facing production use.

## Release Decision

| Target | Decision | Reason |
| --- | --- | --- |
| Local learning lab | **Go** | The setup is reproducible, deterministic without an LLM key, documented, tested, and covered by a runnable evaluation corpus. |
| Public open-source learning release | **Go when `make validate` passes** | Tests, lint, and assistant quality checks are enforced locally and in pull-request CI. |
| Internal pilot with sanitized data | **Conditional** | Add environment-specific access control, centralized telemetry, secret management, ownership, and a rollback plan first. |
| Internet-facing or customer production | **No-go today** | The lab does not yet provide production authentication, durable telemetry backends, tenant isolation, managed secrets, SLO operations, or hardened deployment automation. |

This distinction is intentional. A strong readiness review records what the evidence supports instead of relabeling a useful lab as a production platform.

## One Release Gate

Run the full local gate from the repository root:

```bash
make validate
```

It performs four checks:

1. Builds both service images.
2. Runs both pytest suites.
3. Runs Ruff against both services.
4. Runs the assistant evaluation corpus and fails on any grounding, usefulness, safety, privacy, or honesty regression.

The CI workflow runs the same test, lint, and evaluation categories on every pull request and on pushes to `main`. No provider key or network model call is required for the evaluation gate.

Formatting remains a deliberate author action:

```bash
make format
```

## Evidence Review

| Readiness area | Evidence in this repository | Current boundary |
| --- | --- | --- |
| Reproducibility | Docker Compose, kind manifests, health checks, tests, and copy-paste workflows. | Local and learning environments only. |
| Security | Threat model, safe defaults, secret guidance, and input/output redaction tests. | Pattern redaction is not a data-loss-prevention system; production auth and policy enforcement remain future work. |
| Cost | Deterministic default, bounded evidence windows, prompt limits, and visible cost-control metadata. | Provider token accounting, quotas, budgets, and chargeback are not implemented. |
| Quality | Seven deterministic incident cases and a five-dimension pass/fail rubric. | The corpus is small and does not replace sanitized real incidents, human review, or provider/model evaluation. |
| Observability | Structured logs, request correlation, Prometheus-style metrics, incident walkthroughs, and a production signal contract. | The shared file is a teaching mechanism; no collector or durable logs, metrics, and traces backend is installed. |
| Reliability | Health/readiness endpoints, Kubernetes probes and resources, runbooks, and rollback guidance. | No measured production SLO, alert delivery, autoscaling, multi-zone design, or disaster recovery exercise. |
| Model serving | Provider-compatible configuration and a staged vLLM, Triton, Ray Serve, KServe, and GPU decision framework. | No GPU path is needed or claimed for the default project. |
| Product direction | Open learning core plus a governed evaluation, private deployment, and team workflow direction. | Customer discovery and measured demand must precede platform investment. |

## Promotion Gates For A Real Pilot

Do not promote the current manifests by changing only an image tag. Before an internal pilot, require named owners and evidence for these gates:

- **Identity and access:** authenticate users and services; authorize access to incident evidence; audit sensitive access.
- **Data boundary:** classify allowed evidence, prevent secrets at the source, test redaction, define retention, and document provider handling.
- **Secrets and supply chain:** use a managed secret workflow, pin and scan deployable artifacts, and define rotation and patch ownership.
- **Reliability:** establish baseline SLIs, choose an initial SLO, route actionable alerts, test a runbook, and prove rollback.
- **Observability:** replace shared files with controlled collection and storage; keep evidence queries bounded and attributable.
- **Quality:** add sanitized representative incidents, preserve privacy and safety as hard gates, and version model, prompt, corpus, and thresholds together.
- **Cost:** capture provider identity, latency, token usage, fallback outcome, and cost per successful evaluated analysis; add budgets and quotas.
- **Deployment:** separate environments, use production storage and networking, define backups where state exists, and test recovery.

Any failed privacy or safety gate is a no-go. Other exceptions need a named owner, explicit risk acceptance, a deadline, and a rollback path.

## First 30 Days After This Milestone

The next work should deepen measured contracts before adding infrastructure breadth:

1. Capture provider model, latency, token usage, failure, and fallback metadata without storing prompt content.
2. Expand the evaluation corpus with sanitized incidents and version its acceptance thresholds.
3. Add optional OpenTelemetry collection after log, metric, and trace field contracts are stable.
4. Turn one incident walkthrough into an alert-to-runbook exercise with an owner and measurable recovery result.
5. Build a provider-versus-private-endpoint benchmark harness before adding a GPU deployment example.

vLLM, Triton, Ray Serve, KServe, GPU scheduling, multi-tenancy, and paid platform features stay behind demonstrated demand and the adoption gates already documented in the advanced serving roadmap.

## Day 7 Definition Of Done

- One command runs build, tests, lint, and deterministic assistant evaluations.
- Pull-request CI blocks an evaluation regression.
- The project has an explicit go/no-go decision for each deployment target.
- Local evidence and production gaps are visible in the same scorecard.
- Pilot promotion gates have owners and measurable evidence requirements.
- The next 30 days prioritize instrumentation, evaluation depth, and operational proof over tool accumulation.
