# Advanced Model Serving Roadmap

This guide explains when optional self-hosted inference may be justified for Reliability Lab. The default remains the deterministic analyzer with an optional OpenAI-compatible provider path.

## Decision Inputs

Consider a private endpoint or self-hosted model only when measured evidence identifies a concrete need:

- A privacy or deployment boundary requires controlled infrastructure.
- An approved model must run in a specific environment.
- Sustained traffic makes provider latency or capacity unsuitable for the workload.
- Multiple models need shared routing, scheduling, or evaluation.
- A benchmark shows a clear improvement for the same quality and safety gates.

Do not add GPUs, Kubernetes operators, or serving frameworks simply because they are common in AI infrastructure diagrams.

## Staged Path

### Stage 0: Deterministic And Provider-Compatible

Keep the rule-based analyzer as the default. Use the same evaluation corpus and privacy controls for every optional provider experiment.

### Stage 1: Private Endpoint Benchmark

Test one approved OpenAI-compatible endpoint against the managed-provider and deterministic paths. Measure quality, latency, token usage, fallbacks, throughput, and cost per successful evaluated analysis.

### Stage 2: Single-GPU Experiment

Run one bounded model on one GPU only after the benchmark identifies a specific gap. Record model version, hardware, concurrency, memory behavior, failure handling, and rollback steps.

### Stage 3: Managed Serving

Introduce vLLM, Triton, Ray Serve, or KServe only when a measured orchestration problem requires it. Document the exact problem, acceptance criteria, resource budget, and operational owner.

## Operating Requirements

Before expanding beyond a bounded experiment, define:

- Authentication and authorization for the endpoint.
- Secret management and rotation.
- Model and container version pinning.
- Resource requests, limits, and GPU scheduling policy.
- Queue, latency, error, utilization, and out-of-memory signals.
- Rollback and recovery procedures.
- The same privacy, safety, and evaluation release gates used by the default path.

## Non-Goals

Reliability Lab does not aim to become a general model-serving platform. It keeps optional serving examples small, evidence-driven, and subordinate to the learning path.

## Exit Criteria

Advance a serving stage only when the benchmark, evaluation suite, and operational review agree that the next layer solves a documented problem. Otherwise, keep the simpler provider-compatible path.
