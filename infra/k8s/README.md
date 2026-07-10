# Kubernetes

Week 3 introduces Kubernetes as a new runtime for the same learning lab.

The goal is not to learn every Kubernetes feature. The goal is to understand how the existing local system maps to a cluster:

- `demo-service` runs as a Deployment and exposes a Service.
- `ai-sre-assistant` runs as a Deployment and exposes a Service.
- A ConfigMap holds normal configuration.
- An optional Secret can hold an LLM API key.
- A local PersistentVolumeClaim keeps the shared log-file learning model working in kind.

## Primary Local Target

These manifests are optimized for [kind](https://kind.sigs.k8s.io/): Kubernetes running in Docker containers.

This keeps the Week 3 path close to the existing Docker workflow.

## What Each File Does

- `namespace.yaml`: creates the `ai-infra-starter-kit` namespace.
- `configmap.yaml`: stores non-secret environment variables.
- `secret.example.yaml`: documents the optional `OPENAI_API_KEY` Secret shape. Do not put real keys in this file.
- `storage.yaml`: creates local shared storage for demo logs.
- `demo-service.yaml`: runs and exposes the demo service.
- `ai-sre-assistant.yaml`: runs and exposes the assistant.

## Important Logging Note

The Kubernetes setup intentionally keeps the shared log file from Docker Compose:

```text
/shared/logs/demo-service.log
```

This is useful for learning because the assistant can read the same file that `demo-service` writes.

This is not the production logging pattern. In production, use a logging backend or collector such as OpenTelemetry, Loki, Elasticsearch, CloudWatch, or a managed observability platform.

The shared volume is scoped to the local single-node kind learning path.

## Requirements

- Docker
- kind
- kubectl
- Python 3.10 or newer for `scripts/generate-demo-traffic.py`

Check tools:

```bash
docker --version
kind --version
kubectl version --client
```

## 1. Create A Local Cluster

```bash
kind create cluster --name ai-infra-starter-kit
```

Check the cluster:

```bash
kubectl cluster-info --context kind-ai-infra-starter-kit
```

## 2. Build Local Images

From the repository root:

```bash
docker build -t ai-infra-starter-kit/demo-service:local apps/demo-service
docker build -t ai-infra-starter-kit/ai-sre-assistant:local apps/ai-sre-assistant
```

## 3. Load Images Into kind

kind runs its own container runtime inside the cluster node. Loading the images makes them available to Kubernetes.

```bash
kind load docker-image ai-infra-starter-kit/demo-service:local --name ai-infra-starter-kit
kind load docker-image ai-infra-starter-kit/ai-sre-assistant:local --name ai-infra-starter-kit
```

## 4. Apply Manifests

Apply the base resources first:

```bash
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/configmap.yaml
kubectl apply -f infra/k8s/storage.yaml
```

The assistant works without an LLM key. For the default rule-based assistant, applying the example secret is optional:

```bash
kubectl apply -f infra/k8s/secret.example.yaml
```

For the optional LLM setup and the safer private `secret.local.yaml` workflow, see `../../docs/11-kubernetes-config-and-secrets.md`.

Apply the workloads:

```bash
kubectl apply -f infra/k8s/demo-service.yaml
kubectl apply -f infra/k8s/ai-sre-assistant.yaml
```

## 5. Wait For Apps

```bash
kubectl wait --for=condition=available deployment/demo-service -n ai-infra-starter-kit --timeout=120s
kubectl wait --for=condition=available deployment/ai-sre-assistant -n ai-infra-starter-kit --timeout=120s
```

Inspect what is running:

```bash
kubectl get pods,svc,pvc -n ai-infra-starter-kit
```

For a more complete operations and troubleshooting checklist, see `../../docs/10-kubernetes-operations-runbook.md`.

For a focused guide to probes and resource requests/limits, see `../../docs/12-kubernetes-health-and-resources.md`.

For an end-to-end incident debugging walkthrough, see `../../docs/13-kubernetes-incident-debugging.md`.

## 6. Port Forward Services

Open one terminal for `demo-service`:

```bash
kubectl port-forward svc/demo-service 8000:8000 -n ai-infra-starter-kit
```

Open another terminal for `ai-sre-assistant`:

```bash
kubectl port-forward svc/ai-sre-assistant 8001:8001 -n ai-infra-starter-kit
```

Now the services are available locally:

- `http://localhost:8000`
- `http://localhost:8001`

## 7. Verify Health And Metrics

```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics
curl http://localhost:8001/health
```

## 8. Generate Traffic

From the repository root:

```bash
python scripts/generate-demo-traffic.py --base-url http://localhost:8000
```

## 9. Ask The Assistant

Analyze metrics:

```bash
curl -s -X POST http://localhost:8001/analyze/metrics \
  -H "Content-Type: application/json" \
  -d '{}'
```

Summarize the incident using logs and metrics:

```bash
curl -s -X POST http://localhost:8001/summarize-incident \
  -H "Content-Type: application/json" \
  -d '{"max_lines":120,"use_llm":false}'
```

## 10. Inspect Kubernetes Signals

View logs:

```bash
kubectl logs deployment/demo-service -n ai-infra-starter-kit
kubectl logs deployment/ai-sre-assistant -n ai-infra-starter-kit
```

Describe a pod if something is not ready:

```bash
kubectl describe pod -l app.kubernetes.io/name=demo-service -n ai-infra-starter-kit
```

## 11. Cleanup

Delete the namespace:

```bash
kubectl delete namespace ai-infra-starter-kit
```

Delete the local persistent volume if it remains:

```bash
kubectl delete pv ai-infra-shared-logs
```

Delete the kind cluster:

```bash
kind delete cluster --name ai-infra-starter-kit
```

## Kubernetes Objects In Plain English

- Deployment: keeps the desired number of app pods running.
- Pod: runs one or more containers.
- Service: gives pods a stable network name.
- ConfigMap: stores normal configuration.
- Secret: stores sensitive configuration.
- PersistentVolumeClaim: asks Kubernetes for storage.
- Readiness probe: tells Kubernetes when an app can receive traffic.
- Liveness probe: tells Kubernetes when an app should be restarted.
- Resource requests and limits: describe expected CPU and memory use.

## Not Included Yet

This first Kubernetes step intentionally avoids:

- Helm
- Kustomize
- Ingress
- autoscaling
- service mesh
- Prometheus and Grafana
- GPU scheduling
- vLLM, Triton, Ray, or KServe

Those are later roadmap topics.
