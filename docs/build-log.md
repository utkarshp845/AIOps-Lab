# Build Log

## Day 1 - Simple First, Production-Minded Always

I am building `ai-infra-starter-kit` because AI infrastructure is becoming part of normal software infrastructure, but the learning path often starts too late in the stack.

AI infra is intimidating because beginners are quickly surrounded by model serving frameworks, GPU scheduling, Kubernetes operators, distributed systems, observability, evals, and cost tradeoffs. Those topics matter, but they do not need to arrive all at once.

Simplicity is the edge for this project. The first version uses a small FastAPI service, structured logs, a metrics endpoint, Docker Compose, and an AI SRE Assistant that reads evidence. That is enough to teach the shape of the workflow without hiding the production direction.

Day 1 includes:

- `demo-service` with health, readiness, normal API, simulated errors, latency, memory pressure, logs, and metrics.
- `ai-sre-assistant` with API endpoints, CLI, rule-based analysis, and optional OpenAI-compatible LLM support.
- Docker Compose for local operation.
- Sample logs and questions.
- Docs for architecture, setup, observability, security, cost, and roadmap.

Next comes better observability: richer metrics, incident examples, dashboard basics, and clearer structured logging patterns.

## Week 2, Day 1 - Metrics Cleanup

Today I started Week 2: observability basics.

Week 1 answered the first question: can someone clone the repo, run the local AI infrastructure lab, generate signals, and ask the AI SRE Assistant what happened?

Week 2 starts with a different question: can someone understand what the service is doing from its operational signals?

The first cleanup was the `/metrics` endpoint in `demo-service`.

What changed:

- Moved metrics logic into a dedicated `app/metrics.py` module.
- Added request counters by method, route template, and status code.
- Added histogram-style latency buckets with `_bucket`, `_sum`, and `_count` output.
- Added counters for simulated errors, latency events, and memory pressure events.
- Normalized dynamic paths like `/api/orders/ord-1001` to `/api/orders/{order_id}`.
- Added tests for metrics output, simulation counters, and route label normalization.
- Updated the observability docs with counters, latency buckets, and label cardinality.

Why this matters:

Metrics are not just numbers. The names and labels decide whether the service stays understandable as traffic grows.

A raw path like `/api/orders/ord-1001` looks harmless in a tiny app, but in a real system it can create a new time series for every order ID. That is a high-cardinality label problem. The production-minded version is to expose the route shape, such as `/api/orders/{order_id}`, so the metric explains the endpoint without exploding the number of series.

Lessons learned:

- Logs tell a story about specific events. Metrics show shape, volume, and trend.
- Averages are not enough for latency. Buckets make slow requests easier to spot.
- Good observability starts before dashboards. It starts with stable signal design.
- Keeping this dependency-free for now keeps the Day 1 and Week 2 path beginner-friendly.
- The AI SRE Assistant will be more useful once it can combine log evidence with these cleaner metrics.

What comes next:

- Add incident walkthroughs for error spikes and latency spikes.
- Teach the AI SRE Assistant to read and summarize metrics.
- Add an optional Prometheus/Grafana path without making it required for the local quickstart.

## Week 2, Day 2 - Structured Logs And Request Correlation

Today I continued observability week by improving structured logs.

Day 1 focused on metrics: counters, latency buckets, simulation counters, and label cardinality.

Day 2 focused on logs: how to follow one request through multiple events.

What changed:

- Added request-scoped context for `request_id`.
- Preserved incoming `X-Request-ID` headers when callers provide them.
- Generated a request ID when callers do not provide one.
- Returned the request ID in the `x-request-id` response header.
- Added the same request ID to route-level logs and `request_completed` logs.
- Added a sample correlated request log.
- Expanded observability docs with structured log fields and request correlation.
- Added tests for request ID response headers and correlated route logs.

Why this matters:

Metrics can show that errors increased or latency crossed a threshold. Logs help explain what happened in a specific request.

Without request IDs, logs are just scattered events. With request IDs, a failure becomes a story that can be followed from the route-level error to the final response log.

Lessons learned:

- Request IDs are one of the simplest useful observability patterns.
- Good logs use stable field names, not just readable messages.
- Correlation IDs make both human debugging and AI analysis more grounded.
- Observability starts with signal quality before dashboards or tracing tools.

What comes next:

- Add incident walkthroughs that combine logs and metrics.
- Teach the AI SRE Assistant to summarize metrics alongside logs.
- Keep the local workflow simple while gradually introducing production habits.

## Week 2, Day 3 - Incident Walkthroughs

Today I added incident walkthroughs.

Day 1 cleaned up metrics.

Day 2 improved structured logs and request correlation.

Day 3 connects those signals into operational reasoning.

What changed:

- Added an incident walkthrough index.
- Added an error spike walkthrough.
- Added a latency spike walkthrough.
- Added a memory pressure walkthrough.
- Linked the walkthroughs from the observability basics doc.

Why this matters:

Observability is only useful if it helps someone debug.

Metrics can show that something changed. Logs can explain what happened in a specific request. Request IDs connect related log lines. Incident walkthroughs show how to combine those signals instead of looking at them in isolation.

Lessons learned:

- A good incident workflow starts with symptoms and evidence, not guesses.
- Metrics and logs answer different questions.
- Request IDs make logs more useful during debugging.
- The AI SRE Assistant should follow the same reasoning pattern: facts, evidence, likely causes, safe next steps.

What comes next:

- Teach the AI SRE Assistant to read metrics.
- Let incident summaries combine log evidence and metric evidence.
- Add optional Prometheus and Grafana without making them required for Day 1.

## Week 2, Day 4 - Assistant Reads Metrics

Today I taught the AI SRE Assistant to read metrics.

Day 1 gave the demo service cleaner metrics.

Day 2 made logs easier to correlate with request IDs.

Day 3 added incident walkthroughs.

Day 4 connects the assistant to a second evidence source.

What changed:

- Added a Prometheus text metrics reader.
- Added deterministic metrics analysis.
- Added `POST /analyze/metrics`.
- Updated `POST /summarize-incident` to include logs, metrics, and combined interpretation.
- Added a sample metrics file.
- Documented the new assistant behavior and metrics URL configuration.

Why this matters:

Logs and metrics answer different questions.

Logs explain specific events. Metrics show volume, status distribution, affected paths, and latency shape.

The assistant becomes more useful when it can combine both instead of only reading recent log lines.

Lessons learned:

- AI analysis is only as good as the evidence it receives.
- Deterministic analysis should work before adding LLM enrichment.
- Metrics help the assistant avoid overfitting to one log line.
- The safest assistant behavior is still facts first, guesses second, safe next steps always.

What comes next:

- Improve combined incident summaries with richer examples.
- Add optional Prometheus and Grafana for people ready to see metrics in a dashboard.
- Keep the default local path small and laptop-friendly.

## Week 3, Day 1 - Kubernetes Manifests With kind

Today I started Week 3: Kubernetes basics.

Week 1 built the local learning lab.

Week 2 added observability signals and taught the AI SRE Assistant to read logs and metrics.

Week 3 starts with the same system running in a new runtime.

What changed:

- Added a dedicated Kubernetes namespace.
- Added a ConfigMap for normal app configuration.
- Added an optional Secret example for future LLM keys.
- Added kind-friendly shared log storage for the local learning path.
- Cleaned up the demo-service and AI SRE Assistant manifests.
- Added consistent Kubernetes labels.
- Kept one replica per app to avoid shared-volume confusion.
- Rewrote the Kubernetes README as a kind-first walkthrough.

Why this matters:

Kubernetes adds complexity, but the system shape is the same:

```text
demo-service -> logs/metrics -> ai-sre-assistant -> operational summary
```

The point is not to introduce the whole Kubernetes ecosystem at once. The point is to map the working Docker Compose lab onto Kubernetes primitives: Deployments, Services, ConfigMaps, Secrets, probes, resources, and storage.

Lessons learned:

- Kubernetes is easier to teach when it is tied to a concrete app.
- A Service gives the assistant a stable name for `demo-service`.
- ConfigMaps are a cleaner home for normal environment variables.
- Secrets should be separate, even when the first version works without one.
- Shared file logs are useful for learning, but production should use a real log pipeline.

What comes next:

- Add a local Kubernetes deployment guide as a standalone doc.
- Spend a day on config and secrets.
- Spend a day on health checks, readiness, liveness, and resource limits.
- Then connect Kubernetes logs and metrics back into the observability story.

## Week 3, Day 3 - Kubernetes Operations Runbook

Today I added a Kubernetes operations runbook for the local kind setup.

Day 1 mapped the Docker Compose learning lab into Kubernetes manifests.

Day 3 focuses on the next practical question: once the pods are running, how do you inspect the system without guessing?

What changed:

- Added a Kubernetes operations runbook.
- Documented quick status checks for Deployments, Pods, Services, and PVCs.
- Added health, readiness, metrics, and assistant analysis checks.
- Added troubleshooting flows for `ImagePullBackOff`, pods that are running but not ready, missing logs, missing metrics, pending PVCs, and port-forward issues.
- Added a safe debugging order that starts with read-only inspection.
- Linked the runbook from the root README and Kubernetes walkthrough.

Why this matters:

Kubernetes is easier to learn when each command answers a specific operational question.

`kubectl get pods` is not just a command to memorize. It answers whether the workload exists and what state Kubernetes sees. `kubectl describe` explains scheduling, probes, mounts, and events. `kubectl logs` shows what the app says happened. The assistant analysis brings the application signals back into the same workflow.

Lessons learned:

- Kubernetes debugging should start with evidence, not restarts.
- Pod status, readiness, service endpoints, and application health are related but different signals.
- A Service can exist even when no ready pods are behind it.
- The shared log PVC is useful for learning, but production logging needs a real pipeline.
- The AI SRE Assistant remains more useful when it can cite logs and metrics instead of guessing.

What comes next:

- Spend a focused day on ConfigMaps, Secrets, and environment-specific configuration.
- Expand the health check and resource limit explanation.
- Keep the kind path simple before introducing Helm, Ingress, or observability stacks.

## Week 3, Day 4 - Kubernetes ConfigMaps And Secrets

Today I documented how configuration moves from Docker Compose into Kubernetes.

Day 3 focused on operating the local kind deployment. Day 4 focuses on how the apps receive configuration once they are running in the cluster.

What changed:

- Added a Kubernetes ConfigMaps and Secrets guide.
- Explained which values belong in the ConfigMap and why.
- Explained why `OPENAI_API_KEY` belongs in a Secret.
- Documented the default no-key path where the assistant uses rule-based analysis.
- Added an optional local LLM setup using a private `secret.local.yaml` file.
- Added `.gitignore` protection for the private local Secret file.
- Clarified `configmap.yaml` and `secret.example.yaml` comments.
- Linked the new guide from the README, Kubernetes walkthrough, and operations runbook.

Why this matters:

Kubernetes configuration is easier to understand when it maps back to something familiar. A Docker Compose `.env` file becomes a ConfigMap for normal values and a Secret for sensitive values.

The important production-minded habit is the boundary: commit normal config when it is safe, but never commit real credentials.

Lessons learned:

- ConfigMaps are for normal configuration, not secrets.
- Secrets should be optional when the beginner path can work without them.
- Environment variables from ConfigMaps and Secrets are read when the container starts.
- Restarting a Deployment is the simple way to pick up changed env values.
- The assistant remains useful without an LLM key because deterministic analysis is the default.

What comes next:

- Spend a focused day on probes, health checks, and resource requests/limits.
- Show how Kubernetes decides whether a pod is ready for traffic.
- Keep the local kind path small before adding Helm, Ingress, or external secret managers.

## Week 3, Day 5 - Kubernetes Health Checks And Resources

Today I documented how Kubernetes uses health checks, readiness checks, and resource settings to operate the local learning lab.

Day 4 focused on how configuration reaches the apps. Day 5 focuses on how Kubernetes decides whether those apps are alive, ready for traffic, and running with reasonable CPU and memory expectations.

What changed:

- Added a Kubernetes health checks and resources guide.
- Explained health vs readiness in beginner-friendly terms.
- Documented liveness probes, readiness probes, resource requests, and resource limits.
- Added commands for inspecting Deployments, Pods, events, endpoints, rollouts, and app health endpoints.
- Added troubleshooting notes for pods that are running but not ready, pods that keep restarting, and `OOMKilled` behavior.
- Added small manifest comments around probes and resources.
- Linked the new guide from the README, Kubernetes walkthrough, and operations runbook.

Why this matters:

Kubernetes needs clear signals to operate an app safely. A liveness probe answers whether Kubernetes should restart a container. A readiness probe answers whether the pod should receive traffic. Resource requests help scheduling. Resource limits create local safety boundaries.

Lessons learned:

- Running is not the same as ready.
- Readiness failures should usually remove traffic, not restart the app.
- Liveness probes should be conservative because bad restart behavior can make incidents worse.
- Resource requests are scheduling signals; limits are enforcement boundaries.
- The current values are learning defaults, not production tuning recommendations.

What comes next:

- Connect Kubernetes events, logs, and assistant analysis into a clearer incident workflow.
- Add a small Kubernetes troubleshooting example using the existing simulated failure endpoints.
- Keep autoscaling and HPA for after resource requests are easier to understand.

## Week 3, Day 6 - Kubernetes Incident Debugging

Today I connected the Kubernetes learning path into an incident debugging workflow.

Day 5 focused on probes and resources. Day 6 focuses on what to do when the app is running in Kubernetes but the service still shows failures, latency, or warning signals.

What changed:

- Added a Kubernetes incident debugging walkthrough.
- Documented how to create intentional symptoms with existing simulation endpoints.
- Added a debugging order from Kubernetes state to app health, logs, metrics, and assistant analysis.
- Added commands for inspecting Deployments, Pods, Services, endpoints, PVCs, events, logs, metrics, and assistant summaries.
- Added a debugging map that connects symptoms to first checks and likely interpretations.
- Linked the walkthrough from the README, Kubernetes walkthrough, and operations runbook.

Why this matters:

Kubernetes can tell you what is happening to the workload, but it does not automatically explain what is happening inside the application. Logs and metrics provide that application evidence. The AI SRE Assistant helps summarize those signals into practical operational language.

Lessons learned:

- Start broad with Kubernetes state before narrowing into app behavior.
- A healthy pod can still serve failing endpoints.
- Logs explain specific events; metrics explain shape and volume.
- Assistant output is most useful when it is grounded in collected evidence.
- Good debugging starts with facts before fixes.

What comes next:

- Wrap Week 3 with production-minded Kubernetes next steps.
- Explain what should change before this pattern becomes production-grade.
- Keep advanced tools like Helm, Ingress, HPA, and service mesh as future roadmap items.
