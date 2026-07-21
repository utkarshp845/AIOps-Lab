# Provider Telemetry Contract

Week 5, Day 1 establishes the privacy-safe metadata contract for optional LLM calls.

The assistant already bounded prompts and fell back to deterministic analysis. The missing foundation was a consistent way to answer: which provider path was selected, was a request attempted, did it succeed, how long did it take, did the provider report token usage, and did the deterministic fallback protect the user?

## API Contract

When `use_llm=true`, `/ask`, `/analyze/logs`, and `/summarize-incident` include `llm_telemetry` alongside the existing analysis and cost-control fields.

```json
{
  "llm_telemetry": {
    "provider": "openai",
    "model": "approved-model",
    "configured": true,
    "attempted": true,
    "outcome": "success",
    "request_latency_ms": 842.37,
    "fallback_used": false,
    "fallback_reason": null,
    "usage": {
      "reported": true,
      "input_tokens": 420,
      "output_tokens": 96,
      "total_tokens": 516
    }
  }
}
```

The contract is per request. It is not yet a persistent usage ledger, billing record, Prometheus metric implementation, or cost estimate.

## Field Semantics

| Field | Meaning |
| --- | --- |
| `provider` | Bounded, redacted provider label from configuration. It never contains the base URL. |
| `model` | Bounded, redacted model label when the provider is configured; otherwise `null`. |
| `configured` | Whether the selected provider has the minimum required configuration. |
| `attempted` | Whether the assistant attempted a network request to the provider. |
| `outcome` | One of `success`, `failure`, or `not_configured`. |
| `request_latency_ms` | Provider request duration measured with a monotonic clock; `null` when no request was attempted. |
| `fallback_used` | Whether the final response stayed on the deterministic rule-based path. |
| `fallback_reason` | `provider_not_configured`, `provider_request_failed`, or `null`. |
| `usage.reported` | Whether the provider returned usable token counts. |
| `usage.input_tokens` | Normalized `prompt_tokens`, or `null` when unavailable. |
| `usage.output_tokens` | Normalized `completion_tokens`, or `null` when unavailable. |
| `usage.total_tokens` | Provider total, or the sum of valid input and output counts when both exist. |

Unknown, negative, boolean, or malformed token values are treated as unavailable. Providers may omit usage; omission does not turn a successful analysis into a failure.

## Outcomes And Fallbacks

| Situation | Outcome | Attempted | Fallback |
| --- | --- | --- | --- |
| `LLM_PROVIDER=none` or incomplete configuration | `not_configured` | No | Yes: `provider_not_configured` |
| Valid response with non-empty content | `success` | Yes | No |
| Network, HTTP, parsing, or empty-content failure | `failure` | Yes | Yes: `provider_request_failed` |
| Request sets `use_llm=false` | No LLM telemetry block | No | The deterministic path was explicitly selected, not used as a provider fallback. |

## Privacy Boundary

Provider telemetry may contain only bounded operational metadata.

Allowed:

- Provider and model labels.
- Configuration, attempt, outcome, and fallback state.
- Request latency.
- Numeric token counts.

Forbidden:

- Questions or prompts.
- Log, metric, trace, or incident evidence.
- API keys, authorization headers, or credentials.
- Provider base URLs.
- Model output or failure payloads.
- User, request, workspace, or incident identifiers.

Tests inject secrets into questions, logs, credentials, provider output, and failure messages and verify that those values never enter the telemetry object. The final API response still passes through the existing defense-in-depth redaction boundary.

## Customer And Product Value

This contract supports the commercialization roadmap without creating a surveillance or billing system prematurely:

- Design partners can see whether enrichment succeeded or silently fell back.
- Teams can compare provider latency and token usage against evaluated quality later.
- Product decisions can use cost per successful analysis instead of token price alone.
- Private endpoints and managed providers can use the same normalized outcome contract.

Do not attach customer identifiers to future Prometheus labels. Per-team billing, audit attribution, and durable usage history require an access-controlled event ledger with explicit retention.

## Day 1 Definition Of Done

- Provider and model identity are exposed as bounded, redacted labels.
- Success, failure, unconfigured state, and deterministic fallback are distinguishable.
- Provider request latency uses a monotonic clock.
- OpenAI-compatible token usage is normalized when present and honest when absent.
- No prompt, evidence, credential, endpoint URL, or generated output enters telemetry.
- Both LLM-enabled API flows expose the same contract.
- Success, failure, fallback, usage, latency, and privacy behavior have deterministic tests.

## Remaining Week 5 Sequence

1. Add bounded aggregate counters and latency distributions without high-cardinality labels.
2. Define explicit model pricing inputs and estimated cost metadata without hard-coding unstable prices.
3. Join provider outcomes and cost with evaluation results to calculate cost per successful evaluated analysis.
4. Add a local comparison report across deterministic and configured provider paths.
5. Exercise provider failure and fallback behavior end to end.
6. Close the week with an exit-gate review against the technical and commercialization roadmaps.
