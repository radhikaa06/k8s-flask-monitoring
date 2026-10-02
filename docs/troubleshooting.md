# Troubleshooting

## The method: get, describe, logs, events, exec

Almost every Kubernetes problem is solved by running these five commands in order, from the broadest view to the most detailed.

| Step | Command | Answers |
|---|---|---|
| 1. Get | `kubectl get pods -A` | Which pod is unhappy, and what is its STATUS / RESTARTS? |
| 2. Describe | `kubectl describe pod <name>` | Events at the bottom: scheduling, image pulls, probe failures, OOM kills |
| 3. Logs | `kubectl logs <name>` (add `--previous` after a crash) | What the application itself printed |
| 4. Events | `kubectl get events --sort-by=.lastTimestamp` | Cluster-wide timeline of what just happened |
| 5. Exec | `kubectl exec -it <name> -- sh` | Look inside the running container (files, env, network) |

Two more checks solve most networking problems:

| Check | Command | Healthy result |
|---|---|---|
| Does the Service have pods behind it? | `kubectl get endpoints flask-app-service` | Three `IP:5000` entries |
| Do the labels match? | `kubectl get pods --show-labels` | Pods carry `app=flask-app` |

## Error catalogue

| Symptom | Likely cause | How to confirm | Fix |
|---|---|---|---|
| `ErrImagePull` / `ImagePullBackOff` | Image not inside Minikube, tag typo, or `imagePullPolicy: Always` | `describe` Events: `pull access denied` / `not found` | `minikube image load flask-app:1.0.0`; make the tag match `k8s/deployment.yaml` |
| `CrashLoopBackOff` | App exits on start (bad code, bad config, OOM) | `kubectl logs <pod> --previous` | Fix the error in the logs; for exit code 137 see OOMKilled |
| `OOMKilled` (exit code 137) | Memory above the limit | `describe`: `Last State: Terminated, Reason: OOMKilled` | Raise `limits.memory` or fix the memory leak |
| `Pending` | Not enough CPU or memory for the **requests** on any node | `describe`: `0/1 nodes are available: Insufficient cpu` | Lower requests, scale down, or `minikube start --cpus/--memory` |
| `CreateContainerConfigError` | Referenced ConfigMap or Secret does not exist | `describe`: `configmap "..." not found` | `kubectl apply -f k8s/configmap.yaml` |
| `ContainerCreating` forever | A volume cannot be mounted | `describe`: `FailedMount` | Create the missing ConfigMap (e.g. `grafana-dashboards`) |
| `Running` but `READY 0/1` | Readiness probe failing | `describe`: `Readiness probe failed: ... 503` | Check `/health` with `kubectl port-forward`; check the probe path and port |
| `RESTARTS` keeps increasing | Liveness probe failing, or crashes | `describe`: `failed liveness probe, will be restarted` | Make sure the app answers `/health` in time; increase `initialDelaySeconds` for slow starts |
| Browser cannot reach the app | Tunnel closed, or Service has no endpoints | `kubectl get endpoints flask-app-service` | Keep `minikube service ...` running; fix the selector/labels |
| `connection refused` from kubectl | Cluster stopped or wrong context | `kubectl config current-context` | `minikube start`; `kubectl config use-context minikube` |
| Rollout stuck | New pods never become ready | `kubectl rollout status deployment/flask-app` | `kubectl rollout undo deployment/flask-app`, then investigate the new pod |
| Prometheus target `DOWN` | Pod not ready, wrong port, or `/metrics` missing | Status > Targets shows the error text | Port must be named `http`; check `curl <pod>:5000/metrics` |
| Prometheus cAdvisor `403` | RBAC missing `nodes/proxy` | Status > Targets | Re-apply `monitoring/10-prometheus.yaml` |
| Grafana panel `No data` | Wrong query, wrong time range, or no traffic yet | Run the query in Prometheus > Graph | Generate load with `scripts/load.sh`; set the time range to the last 15 minutes |
| `minikube start` fails | Docker Desktop not running or short of memory | Error message mentions the driver or memory | Start Docker Desktop; lower `--memory`; `minikube delete` and retry |
| Shell script fails with `$'\r': command not found` | Windows (CRLF) line endings | `file scripts/deploy.sh` | `.gitattributes` prevents it; fix existing files with `git add --renormalize .` |

## Useful one-liners

```bash
kubectl get all -n monitoring                         # everything in a namespace
kubectl logs -l app=flask-app --tail=20 --prefix      # last logs from every replica
kubectl top pods -A                                   # live CPU/memory (metrics-server)
kubectl get pod <name> -o yaml                        # the full live object
kubectl explain deployment.spec.strategy              # built-in documentation for any field
minikube dashboard                                    # Kubernetes web UI
```
