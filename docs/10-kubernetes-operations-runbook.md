# Kubernetes Operations Runbook

Week 3 Day 3 is about operating the local Kubernetes version of the lab after it is deployed.

The goal is not to memorize every `kubectl` command. The goal is to learn the small set of checks that answer practical questions:

- Are the apps running?
- Are they ready to receive traffic?
- Can the services talk to each other?
- Are logs and metrics still available?
- What should I inspect first when something breaks?

This runbook assumes you already created the kind cluster, loaded local images, and applied the manifests from `../infra/k8s/README.md`.

## Namespace

All Kubernetes resources for this project run in one namespace:

```bash
kubectl get all -n ai-infra-starter-kit
```

For a shorter local session, you can set the namespace on your current context:

```bash
kubectl config set-context --current --namespace=ai-infra-starter-kit
```

The rest of this guide keeps `-n ai-infra-starter-kit` in commands so each example is explicit and copy-paste friendly.

## Quick Status Check

Start with the cluster objects that explain most local issues:

```bash
kubectl get deployments,pods,svc,pvc -n ai-infra-starter-kit
```

What you want to see:

- `deployment/demo-service` has `1/1` available.
- `deployment/ai-sre-assistant` has `1/1` available.
- both pods are `Running`.
- both services exist.
- the shared log PVC is `Bound`.

Then confirm rollout status:

```bash
kubectl rollout status deployment/demo-service -n ai-infra-starter-kit
kubectl rollout status deployment/ai-sre-assistant -n ai-infra-starter-kit
```

## Health, Readiness, And Metrics

Port-forward both services in separate terminals:

```bash
kubectl port-forward svc/demo-service 8000:8000 -n ai-infra-starter-kit
```

```bash
kubectl port-forward svc/ai-sre-assistant 8001:8001 -n ai-infra-starter-kit
```

Check the app-level signals:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/metrics
curl http://localhost:8001/health
```

These checks separate Kubernetes health from application health:

- Kubernetes can show a pod is running.
- `/ready` tells you whether the app considers itself ready.
- `/metrics` tells you whether operational signals are being emitted.

## Generate A Small Incident

Create logs, errors, and latency from your laptop:

```bash
python scripts/generate-demo-traffic.py --base-url http://localhost:8000
```

Ask the assistant to analyze metrics:

```bash
curl -s -X POST http://localhost:8001/analyze/metrics \
  -H "Content-Type: application/json" \
  -d '{}'
```

Ask for a combined incident summary:

```bash
curl -s -X POST http://localhost:8001/summarize-incident \
  -H "Content-Type: application/json" \
  -d '{"max_lines":120,"use_llm":false}'
```

The important learning path is the same as Docker Compose:

```text
traffic -> demo-service logs/metrics -> ai-sre-assistant analysis
```

Kubernetes changes the runtime, not the operational reasoning model.

## Read Kubernetes Logs

View recent logs from each Deployment:

```bash
kubectl logs deployment/demo-service -n ai-infra-starter-kit --tail=50
kubectl logs deployment/ai-sre-assistant -n ai-infra-starter-kit --tail=50
```

Follow logs while generating traffic:

```bash
kubectl logs deployment/demo-service -n ai-infra-starter-kit --follow
```

For this learning lab, the assistant also reads the shared file at:

```text
/shared/logs/demo-service.log
```

That file-based path is intentionally local and beginner-friendly. In production, logs should flow through a collector or logging backend instead of a shared application volume.

## Inspect Services

Services give pods stable names inside the cluster.

Check service objects:

```bash
kubectl get svc -n ai-infra-starter-kit
```

Check service endpoints:

```bash
kubectl get endpoints demo-service -n ai-infra-starter-kit
kubectl get endpoints ai-sre-assistant -n ai-infra-starter-kit
```

If a Service has no endpoints, Kubernetes has not found any ready pods behind it. Check pod labels, readiness probes, and pod status.

## Inspect Configuration

Normal configuration lives in the ConfigMap:

```bash
kubectl describe configmap ai-infra-starter-kit-config -n ai-infra-starter-kit
```

Sensitive configuration belongs in a Secret:

```bash
kubectl get secret ai-sre-assistant-secrets -n ai-infra-starter-kit
```

Do not paste real API keys into screenshots, tweets, issues, or pull requests.

## Inspect Storage

The local kind setup uses a shared PersistentVolumeClaim so the assistant can read the demo-service log file.

Check the claim:

```bash
kubectl get pvc -n ai-infra-starter-kit
```

Describe it if it is not `Bound`:

```bash
kubectl describe pvc shared-logs -n ai-infra-starter-kit
```

This is a learning bridge from Docker Compose to Kubernetes. It is not the recommended production logging architecture.

## Troubleshooting By Symptom

### Pods Are Stuck In ImagePullBackOff

Likely cause: kind cannot see the local Docker image.

Check:

```bash
kubectl describe pod -l app.kubernetes.io/name=demo-service -n ai-infra-starter-kit
```

Fix:

```bash
docker build -t ai-infra-starter-kit/demo-service:local apps/demo-service
docker build -t ai-infra-starter-kit/ai-sre-assistant:local apps/ai-sre-assistant
kind load docker-image ai-infra-starter-kit/demo-service:local --name ai-infra-starter-kit
kind load docker-image ai-infra-starter-kit/ai-sre-assistant:local --name ai-infra-starter-kit
kubectl rollout restart deployment/demo-service -n ai-infra-starter-kit
kubectl rollout restart deployment/ai-sre-assistant -n ai-infra-starter-kit
```

### Pods Are Running But Not Ready

Likely cause: readiness probes are failing or the app is not listening on the expected port.

Check:

```bash
kubectl describe pod -l app.kubernetes.io/name=demo-service -n ai-infra-starter-kit
kubectl logs deployment/demo-service -n ai-infra-starter-kit --tail=100
```

Look for failed readiness probe events, startup errors, or port mismatches.

### Assistant Cannot Read Logs

Likely causes:

- traffic has not generated any demo-service logs yet.
- the shared PVC is not bound.
- the log path does not match `DEMO_SERVICE_LOG_PATH`.
- one of the pods does not have the shared volume mounted.

Check:

```bash
kubectl get pvc -n ai-infra-starter-kit
kubectl describe configmap ai-infra-starter-kit-config -n ai-infra-starter-kit
kubectl logs deployment/demo-service -n ai-infra-starter-kit --tail=50
kubectl logs deployment/ai-sre-assistant -n ai-infra-starter-kit --tail=50
```

Then generate traffic again:

```bash
python scripts/generate-demo-traffic.py --base-url http://localhost:8000
```

### Assistant Cannot Read Metrics

Likely causes:

- `demo-service` is not ready.
- the `demo-service` Service has no endpoints.
- `DEMO_SERVICE_METRICS_URL` is wrong.

Check:

```bash
kubectl get endpoints demo-service -n ai-infra-starter-kit
kubectl describe configmap ai-infra-starter-kit-config -n ai-infra-starter-kit
curl http://localhost:8000/metrics
```

The expected in-cluster metrics URL is:

```text
http://demo-service:8000/metrics
```

### PVC Is Pending

Likely cause: Kubernetes could not bind the claim to local storage.

Check:

```bash
kubectl get pv
kubectl describe pvc shared-logs -n ai-infra-starter-kit
```

For this repo, `infra/k8s/storage.yaml` includes a kind-friendly local PersistentVolume. Reapply it if needed:

```bash
kubectl apply -f infra/k8s/storage.yaml
```

### Port Forward Fails

Likely causes:

- the Service name is wrong.
- the namespace is missing.
- the local port is already in use.

Check:

```bash
kubectl get svc -n ai-infra-starter-kit
```

Use different local ports if needed:

```bash
kubectl port-forward svc/demo-service 18000:8000 -n ai-infra-starter-kit
kubectl port-forward svc/ai-sre-assistant 18001:8001 -n ai-infra-starter-kit
```

Then call:

```bash
curl http://localhost:18000/health
curl http://localhost:18001/health
```

## Safe Debugging Order

Use this order when something is wrong:

1. `kubectl get deployments,pods,svc,pvc -n ai-infra-starter-kit`
2. `kubectl describe pod ...`
3. `kubectl logs deployment/...`
4. app health endpoints through port-forward
5. metrics endpoint
6. assistant analysis endpoint
7. config and storage checks

Start with read-only inspection. Restart or delete resources only after the evidence points to a clear cause.

## Screenshot Checklist

Useful screenshots for a build-in-public update:

- `kubectl get deployments,pods,svc,pvc -n ai-infra-starter-kit`
- `kubectl rollout status deployment/demo-service -n ai-infra-starter-kit`
- `curl http://localhost:8000/health` and `curl http://localhost:8000/metrics`
- `POST /analyze/metrics` response from the assistant
- `kubectl logs deployment/demo-service --tail=20`
- the troubleshooting section in this runbook

Redact secrets, tokens, local usernames, and any real API keys before posting.

## Production-Minded Notes

This local Kubernetes setup intentionally avoids production add-ons for now.

Later versions can add:

- centralized logging
- OpenTelemetry
- Prometheus and Grafana
- Ingress
- autoscaling
- resource tuning
- secret management
- deployment strategies

For Day 3, the important production habit is simpler: learn how to inspect the system before changing it.
