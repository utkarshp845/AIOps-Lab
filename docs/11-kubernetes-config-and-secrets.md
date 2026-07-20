# Kubernetes ConfigMaps And Secrets

Week 3 Day 4 explains how configuration moves from local Docker Compose into Kubernetes.

The goal is to keep the learning path simple while introducing a real production habit: normal configuration and sensitive configuration should be handled differently.

## The Mental Model

In Docker Compose, this project uses `.env` values and service environment variables.

In Kubernetes, the same idea becomes:

```text
normal config  -> ConfigMap -> container environment variables
sensitive data -> Secret    -> container environment variables
```

For this repo:

- `infra/k8s/configmap.yaml` stores values that are safe to commit.
- `infra/k8s/secret.example.yaml` documents the shape of an optional secret.
- `infra/k8s/secret.local.yaml` is the suggested private local filename for a real key and is ignored by git.

## What Belongs In A ConfigMap

A ConfigMap is for normal, non-secret configuration.

Current values:

| Key | Why it exists |
| --- | --- |
| `DEMO_SERVICE_LOG_PATH` | Tells both services where the shared demo-service log file lives. |
| `DEMO_SERVICE_METRICS_URL` | Tells the assistant where to fetch demo-service metrics inside the cluster. |
| `LLM_PROVIDER` | Controls whether the assistant uses rule-based analysis, OpenAI-compatible APIs, or Ollama. |
| `OPENAI_BASE_URL` | Stores the OpenAI-compatible API base URL. |
| `MODEL_NAME` | Stores the model name used when an LLM provider is enabled. |
| `LLM_MAX_LOG_ENTRIES` | Bounds how many recent log records can enter an optional LLM prompt. |
| `LLM_MAX_PROMPT_CHARS` | Caps the assembled prompt size before an optional provider request. |

Inspect the ConfigMap:

```bash
kubectl describe configmap aiops-lab-config -n aiops-lab
```

The default `LLM_PROVIDER` is `none` so the project works without an API key. The default cost controls keep provider prompts bounded when a user enables LLM enrichment.

## What Belongs In A Secret

A Secret is for sensitive values such as API keys, tokens, credentials, and certificates.

For this project, the only optional secret is:

```text
OPENAI_API_KEY
```

The assistant deployment marks this secret key as optional. That means Kubernetes can start the app even when the secret is missing, and the assistant falls back to deterministic rule-based analysis.

Inspect whether the Secret exists:

```bash
kubectl get secret ai-sre-assistant-secrets -n aiops-lab
```

Do not print, screenshot, tweet, or commit real secret values.

## Default Local Setup Without An LLM Key

The default Kubernetes path needs no key:

```bash
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/configmap.yaml
kubectl apply -f infra/k8s/storage.yaml
kubectl apply -f infra/k8s/demo-service.yaml
kubectl apply -f infra/k8s/ai-sre-assistant.yaml
```

This keeps the beginner path accessible:

```text
LLM_PROVIDER=none
OPENAI_API_KEY is not required
assistant uses rule-based analysis
```

Verify the assistant still works:

```bash
curl -s -X POST http://localhost:8001/summarize-incident \
  -H "Content-Type: application/json" \
  -d '{"max_lines":120,"use_llm":false}'
```

## Optional OpenAI-Compatible LLM Setup

Only do this if you want richer LLM analysis.

Set a local environment variable first.

Bash:

```bash
export OPENAI_API_KEY="your-key-here"
```

PowerShell:

```powershell
$env:OPENAI_API_KEY="your-key-here"
```

Create a private local Secret manifest:

```bash
kubectl create secret generic ai-sre-assistant-secrets \
  --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
  -n aiops-lab \
  --dry-run=client \
  -o yaml > infra/k8s/secret.local.yaml
```

PowerShell:

```powershell
kubectl create secret generic ai-sre-assistant-secrets `
  --from-literal=OPENAI_API_KEY="$env:OPENAI_API_KEY" `
  -n aiops-lab `
  --dry-run=client `
  -o yaml > infra/k8s/secret.local.yaml
```

Apply the private Secret:

```bash
kubectl apply -f infra/k8s/secret.local.yaml
```

Enable the provider in the ConfigMap:

```bash
kubectl patch configmap aiops-lab-config \
  -n aiops-lab \
  --type merge \
  -p '{"data":{"LLM_PROVIDER":"openai"}}'
```

Restart the assistant so it reads the updated environment variables:

```bash
kubectl rollout restart deployment/ai-sre-assistant -n aiops-lab
kubectl rollout status deployment/ai-sre-assistant -n aiops-lab
```

Why restart? Environment variables from ConfigMaps and Secrets are read when the container starts. Updating the ConfigMap or Secret does not automatically update an already-running process.

## Optional Ollama Setup

Ollama support is still optional and local-experiment focused.

The assistant treats `LLM_PROVIDER=ollama` as configured when it has a base URL and model name. In a future Kubernetes lesson, this can be expanded into a cleaner in-cluster local model path.

For now, keep Day 4 focused on the config pattern rather than model serving.

## How The Deployment Reads Config

The assistant Deployment uses `valueFrom` to wire specific keys into the container environment.

Example shape:

```yaml
env:
  - name: LLM_PROVIDER
    valueFrom:
      configMapKeyRef:
        name: aiops-lab-config
        key: LLM_PROVIDER
  - name: OPENAI_API_KEY
    valueFrom:
      secretKeyRef:
        name: ai-sre-assistant-secrets
        key: OPENAI_API_KEY
        optional: true
```

This makes the app image reusable. The image does not need to be rebuilt when config changes.

## Troubleshooting

### The Assistant Still Uses Rule-Based Analysis

Check the provider value:

```bash
kubectl describe configmap aiops-lab-config -n aiops-lab
```

If `LLM_PROVIDER=none`, the assistant is behaving as configured.

Check whether the Secret exists:

```bash
kubectl get secret ai-sre-assistant-secrets -n aiops-lab
```

Restart the Deployment after changing ConfigMaps or Secrets:

```bash
kubectl rollout restart deployment/ai-sre-assistant -n aiops-lab
```

### The Secret Exists But The LLM Request Fails

Check assistant logs without printing the key:

```bash
kubectl logs deployment/ai-sre-assistant -n aiops-lab --tail=100
```

Likely causes:

- `LLM_PROVIDER` is still `none`.
- `OPENAI_BASE_URL` is wrong.
- `MODEL_NAME` is wrong for the provider.
- the API key is invalid or expired.
- the network cannot reach the provider.

### I Accidentally Created A Bad Secret

Delete and recreate the Secret:

```bash
kubectl delete secret ai-sre-assistant-secrets -n aiops-lab
kubectl apply -f infra/k8s/secret.local.yaml
kubectl rollout restart deployment/ai-sre-assistant -n aiops-lab
```

Do not commit `infra/k8s/secret.local.yaml`.

## Safe Rules For This Repo

- Commit ConfigMaps when values are not sensitive.
- Commit `secret.example.yaml` only as documentation.
- Never commit real API keys.
- Prefer `kubectl create secret ... --from-literal` for local experiments.
- Restart pods after changing environment variables from ConfigMaps or Secrets.
- Redact secret names, tokens, and local paths in screenshots when needed.

## Production-Minded Notes

This repo intentionally starts with Kubernetes-native ConfigMaps and Secrets because they are the smallest useful primitives.

In production, teams often add:

- external secret managers
- sealed secrets or encrypted secrets
- environment-specific overlays
- access controls around who can read secrets
- secret rotation policies
- audit logging

Those are later steps. Day 4 is about understanding the boundary between normal config and sensitive config.
