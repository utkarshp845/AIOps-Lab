# Kubernetes Health Checks And Resources

Week 3 Day 5 explains how Kubernetes decides whether an app is healthy, ready for traffic, and running with reasonable CPU and memory expectations.

The goal is not to tune production values yet. The goal is to understand the first useful operating model:

```text
health endpoint -> liveness probe -> restart decision
ready endpoint  -> readiness probe -> traffic decision
requests        -> scheduling expectation
limits          -> local safety boundary
```

## Why This Matters

Running a container is only the beginning.

Kubernetes continuously asks operational questions:

- Is the container still alive?
- Is the app ready to receive traffic?
- Should this pod be included behind the Service?
- How much CPU and memory should the scheduler expect?
- What should happen if the container exceeds its memory limit?

Those questions are the bridge from "my app runs" to "my app can be operated."

## Health vs Readiness

Health and readiness are related, but they are not the same signal.

| Signal | Question it answers | Kubernetes behavior |
| --- | --- | --- |
| Health | Is the process alive? | Restart the container if liveness fails. |
| Readiness | Can this pod receive traffic? | Remove the pod from Service endpoints if readiness fails. |

For `demo-service`:

```text
GET /health -> liveness probe
GET /ready  -> readiness probe
```

For `ai-sre-assistant`, the first Kubernetes lesson uses `/health` for both probes because the assistant does not yet have a separate dependency readiness check.

## Liveness Probe

A liveness probe tells Kubernetes when to restart a container.

From `demo-service`:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 10
  periodSeconds: 20
  timeoutSeconds: 3
  failureThreshold: 3
```

In plain English:

- wait 10 seconds before checking after startup.
- check every 20 seconds.
- wait up to 3 seconds for a response.
- restart after 3 failed checks.

A liveness probe should be conservative. If it is too aggressive, Kubernetes can restart a slow but recovering app and make an incident worse.

## Readiness Probe

A readiness probe tells Kubernetes whether the pod should receive traffic.

From `demo-service`:

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: http
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3
```

If readiness fails, Kubernetes does not need to restart the container. It can simply stop sending traffic to that pod until it becomes ready again.

That is why readiness is often the better place to check dependencies such as databases, queues, or required downstream services.

## Resource Requests And Limits

This repo uses small resource values because the local kind path should work on a normal laptop.

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 256Mi
```

What these mean:

| Field | Meaning |
| --- | --- |
| `requests.cpu` | CPU Kubernetes uses for scheduling decisions. |
| `requests.memory` | Memory Kubernetes expects the pod to need. |
| `limits.cpu` | CPU ceiling. The container may be throttled if it uses too much. |
| `limits.memory` | Memory ceiling. The container can be killed if it exceeds this. |

Useful conversions:

- `100m` CPU means 0.1 CPU core.
- `500m` CPU means 0.5 CPU core.
- `128Mi` means 128 mebibytes of memory.
- `256Mi` means 256 mebibytes of memory.

## Inspect Probes And Resources

Describe the Deployment:

```bash
kubectl describe deployment demo-service -n aiops-lab
kubectl describe deployment ai-sre-assistant -n aiops-lab
```

Describe a pod:

```bash
kubectl describe pod -l app.kubernetes.io/name=demo-service -n aiops-lab
```

Check events:

```bash
kubectl get events -n aiops-lab --sort-by=.lastTimestamp
```

Check pod status:

```bash
kubectl get pods -n aiops-lab
```

Check Service endpoints:

```bash
kubectl get endpoints demo-service -n aiops-lab
kubectl get endpoints ai-sre-assistant -n aiops-lab
```

If a pod is running but not ready, it may not appear as a ready endpoint behind the Service.

## Verify App Endpoints

Port-forward the demo service:

```bash
kubectl port-forward svc/demo-service 8000:8000 -n aiops-lab
```

Check health and readiness:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

Port-forward the assistant:

```bash
kubectl port-forward svc/ai-sre-assistant 8001:8001 -n aiops-lab
```

Check assistant health:

```bash
curl http://localhost:8001/health
```

## Restart And Watch A Rollout

Restart a Deployment:

```bash
kubectl rollout restart deployment/demo-service -n aiops-lab
```

Watch rollout status:

```bash
kubectl rollout status deployment/demo-service -n aiops-lab
```

Watch pods:

```bash
kubectl get pods -n aiops-lab --watch
```

This is a useful way to see readiness in action. Kubernetes starts the new pod, waits for it to become ready, and then the Deployment becomes available.

## Troubleshooting

### Pod Is Running But Not Ready

Check events and probe failures:

```bash
kubectl describe pod -l app.kubernetes.io/name=demo-service -n aiops-lab
```

Then check the app endpoint directly through port-forward:

```bash
curl http://localhost:8000/ready
```

Likely causes:

- the app is not listening on the expected port.
- the readiness path is wrong.
- the app needs more time before it can serve traffic.
- a dependency readiness check is failing.

### Pod Keeps Restarting

Check restart count:

```bash
kubectl get pods -n aiops-lab
```

Describe the pod:

```bash
kubectl describe pod -l app.kubernetes.io/name=demo-service -n aiops-lab
```

Check logs:

```bash
kubectl logs deployment/demo-service -n aiops-lab --tail=100
```

Likely causes:

- liveness probe is failing.
- the app is crashing on startup.
- memory limit is too low.
- the container cannot write or read a mounted path.

### Pod Shows OOMKilled

`OOMKilled` usually means the container exceeded its memory limit.

Check pod details:

```bash
kubectl describe pod -l app.kubernetes.io/name=demo-service -n aiops-lab
```

In a real system, next steps might include:

- checking memory metrics.
- looking for leaks or large allocations.
- increasing limits only after understanding the workload.
- adding better memory instrumentation.

For this local learning lab, keep the lesson simple: memory limits are safety rails, not a replacement for understanding memory behavior.

## Safe Defaults For This Project

The starter manifests intentionally use one replica and small resource settings:

- one replica keeps the shared log volume easy to understand.
- small requests work on a laptop.
- limits prevent runaway local containers.
- probes introduce Kubernetes operating behavior without adding more tools.

These values are not production recommendations. They are learning defaults.

## Production-Minded Notes

In production, probe and resource tuning should be based on evidence:

- real startup time.
- normal and peak latency.
- dependency behavior.
- CPU and memory usage over time.
- failure modes during incidents.

Future roadmap items can build on this:

- Prometheus metrics for resource usage.
- dashboards for latency and error rates.
- Horizontal Pod Autoscaling.
- startup probes for slow-starting apps.
- separate readiness checks for external dependencies.

For Day 5, the important idea is this: Kubernetes needs clear signals to operate your app safely.
