# Cost Optimization Basics

Week 4, Day 3 adds practical cost controls for the AI SRE Assistant.

The goal is not to build a usage-accounting platform. The goal is to make the first cost drivers visible and controllable before the project introduces heavier production tooling.

## Cost Model

In this project, the cheapest path is the default path:

```text
logs / metrics -> rule-based analysis -> response
```

That path runs locally and does not require a external LLM provider.

When an OpenAI-compatible provider is enabled, the flow changes:

```text
logs / metrics -> rule-based analysis -> bounded LLM prompt -> provider response
```

At that point, cost is mostly shaped by:

- whether the assistant calls an LLM at all.
- which model is configured.
- how many log entries are included in the prompt.
- how large the prompt becomes after evidence is serialized.
- how often callers request LLM enrichment.
- provider retries, failures, and latency.

## Defaults

The default `.env.example` keeps provider calls disabled:

```text
LLM_PROVIDER=none
```

That means the assistant uses deterministic rule-based analysis unless a user explicitly enables a provider.

When provider calls are enabled, the assistant applies two budget controls:

```text
LLM_MAX_LOG_ENTRIES=50
LLM_MAX_PROMPT_CHARS=12000
```

`LLM_MAX_LOG_ENTRIES` limits how many recent log records can be included in the LLM prompt.

`LLM_MAX_PROMPT_CHARS` caps the assembled user prompt before the provider request. If the evidence is too large, the assistant truncates it and returns an `llm_notice` explaining that cost controls limited the prompt.

These are character limits, not exact token limits. They are intentionally simple because the project supports any OpenAI-compatible provider and should remain easy to run locally.

## Request-Level Controls

Every log analysis endpoint already supports `use_llm`.

For the lowest-cost path, set it to `false`:

```bash
curl -s -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What failed recently?","max_lines":120,"use_llm":false}'
```

For LLM-enriched analysis, leave `use_llm` enabled and configure a provider:

```bash
curl -s -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What failed recently?","max_lines":120,"use_llm":true}'
```

When `use_llm=true`, the API response includes `llm_cost_controls` so callers can see the prompt limits that were active for that request.

## Why This Matters

AI infrastructure cost can grow in places that are easy to miss.

A single incident summary can be cheap. Repeating that summary on every refresh, sending hundreds of log lines, using a large model by default, or retrying failed provider calls can turn the same workflow into a larger bill.

The first production-minded habit is to make the call boundary explicit:

- Do we need an LLM for this request?
- Is the rule-based answer good enough?
- Are we sending only the evidence needed for the question?
- Are prompt limits visible to the caller?
- Are failures falling back safely instead of retrying blindly?

## Practical Checklist

For local learning:

- keep `LLM_PROVIDER=none` unless testing provider behavior.
- use `use_llm=false` for repeatable smoke tests and demos.
- keep `MODEL_NAME` on a small or inexpensive model when experimenting.
- lower `LLM_MAX_LOG_ENTRIES` when logs are noisy.
- lower `LLM_MAX_PROMPT_CHARS` when latency or cost matters more than detail.

For production planning:

- track request counts by endpoint and caller.
- track provider calls separately from local rule-based responses.
- record prompt and completion token usage when the provider returns it.
- add rate limits and quotas before exposing the assistant broadly.
- consider caching repeated incident summaries.
- use model routing only after the simple default path is measured.
- alert on unexpected provider call volume.

## Relationship To Security

Cost controls and security controls overlap.

Sending less evidence to an external provider reduces spend, latency, and data exposure. Redaction remains the backup control, but the stronger pattern is to avoid sending unnecessary data in the first place.

Day 2 redaction answers: what if sensitive data appears in evidence?

Day 3 cost controls answer: how much evidence should leave the local system at all?

## Current Limits

The current implementation is intentionally lightweight:

- prompt limits use characters, not exact model tokenizer counts.
- no provider-specific pricing table is included.
- no usage dashboard is included.
- no cache is included yet.
- no per-user quota system is included yet.

Those are good future steps, but they are easier to explain after the basic call boundary and prompt budget are visible.
