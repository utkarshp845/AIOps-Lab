# Security Policy

Reliability Lab is a learning project, but security issues still matter.

This repo intentionally starts local and simple. Please do not treat the default Docker Compose or kind setup as production-ready.

## Supported Versions

The public `main` branch is the supported version for security reports.

Older branches and build-in-public feature branches are learning snapshots and may not receive fixes after they are merged or closed.

## Reporting A Vulnerability

If you find a security issue, please do not open a public issue with sensitive details.

Use GitHub private vulnerability reporting if it is enabled for the repository. If it is not enabled, contact the repository owner directly before publishing details.

Include:

- a short description of the issue.
- affected files or commands.
- steps to reproduce.
- expected impact.
- whether any secret, token, or sensitive log content is involved.

Do not include real API keys, tokens, credentials, private logs, or sensitive data in a report.

## Public Issues And Pull Requests

Safe to include:

- fake example keys.
- redacted logs.
- local-only reproduction steps.
- screenshots with secrets removed.

Do not include:

- real `OPENAI_API_KEY` values.
- `.env` contents with secrets.
- `infra/k8s/secret.local.yaml`.
- cloud credentials.
- private cluster details.
- sensitive logs sent to an LLM provider.

## Project Scope

The first versions of this project are intentionally local:

- Docker Compose for Day 1.
- kind for local Kubernetes learning.
- optional OpenAI-compatible LLM provider.
- deterministic rule-based fallback when no LLM key is configured.

Production deployments need additional controls such as authentication, network policy, RBAC, secret management, log redaction, dependency scanning, and assistant evaluation.

## Security Principles

- Keep real secrets out of git.
- Prefer deterministic local behavior when possible.
- Redact sensitive logs before sharing them.
- Treat assistant output as advice, not authority.
- Prefer read-only debugging commands first.
- Avoid destructive commands unless the operator explicitly chooses them.
- Do not send sensitive logs to external LLM providers without review.

## Current Known Limitations

- Local services are not authenticated.
- The kind setup uses port-forwarding for local access.
- The local Kubernetes path uses a shared PVC for logs as a learning bridge.
- Kubernetes Secrets are used as a first teaching primitive, not as a complete production secret-management system.
- The AI SRE Assistant includes focused pattern-based redaction, but not a full data loss prevention, policy, or evaluation layer.

These are intentional for the early learning path and should be addressed before production use.
