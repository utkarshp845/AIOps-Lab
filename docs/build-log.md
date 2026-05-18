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
