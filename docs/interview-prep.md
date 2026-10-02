# Interview Preparation

## The 60-second project pitch

"I built a small Flask web app and focused on the DevOps around it. I containerised it with a slim, non-root Docker image and deployed it to a local Kubernetes cluster on Minikube. A Deployment runs three replicas with readiness and liveness probes and CPU and memory limits, and a NodePort Service load-balances across them. For monitoring, I set up Prometheus and Grafana with plain YAML: Prometheus discovers pods through the Kubernetes API and scrapes container CPU and memory from cAdvisor plus request metrics from the app, and Grafana shows them on a provisioned dashboard. Then I tested failure: deleting pods, making the health check fail, deploying a broken image and setting a memory limit too low. I used describe, logs and events to diagnose each one, and rollbacks to recover."

## Core questions

### Why is Kubernetes used?

Running one container is easy; running many reliably is hard. Kubernetes is a container orchestrator. You declare the desired state ("3 replicas of this image with these limits") and its controllers keep making the real state match: they restart crashed containers, replace lost pods, schedule pods onto nodes with free capacity, load-balance traffic through Services, roll out new versions without downtime and roll them back. Doing all of that by hand with `docker run` does not scale.

### What is the difference between a Pod, a Deployment and a Service?

- **Pod:** the smallest deployable unit, one or more containers sharing an IP and storage. Pods are temporary: when one dies it is replaced by a new pod with a new name and IP, never repaired.
- **Deployment:** manages pods through a ReplicaSet. It keeps the replica count, and handles rolling updates and rollbacks. You almost never create bare pods.
- **Service:** a stable virtual IP and DNS name (`flask-app-service`) that load-balances to all **ready** pods matching its label selector. It solves the problem that pod IPs keep changing.

In my project the Deployment creates 3 pods labelled `app: flask-app`, and the Service selects that label.

### How do replicas work?

`replicas: 3` is the desired state. The Deployment creates a ReplicaSet whose controller runs a reconciliation loop: it counts the pods matching its selector and creates or deletes pods until the count is 3. Scaling is just changing that number (`kubectl scale` or editing the YAML). Replicas give availability (one pod can die without an outage) and capacity (the Service spreads requests across them, as my Grafana "requests by pod" panel shows).

### How does Kubernetes handle pod failure?

There are two levels:

1. **Container crash or failed liveness probe:** the kubelet on the node restarts the container inside the same pod (`RESTARTS` goes up). Repeated crashes lead to `CrashLoopBackOff`, with growing delays between restarts.
2. **Pod deleted, evicted, or its node lost:** the ReplicaSet sees fewer pods than desired and creates a replacement pod, possibly on another node.

Meanwhile the readiness probe removes unhealthy pods from the Service, so users are not sent to them. I demonstrated this by deleting a pod and watching a new one appear within seconds.

### What is the difference between liveness and readiness probes?

- **Readiness:** "Can this pod take traffic now?" If it fails, the pod is removed from the Service endpoints but **not** restarted. Useful during startup or temporary overload.
- **Liveness:** "Is this container broken beyond self-recovery?" If it fails, the container is **restarted**. Useful for deadlocks or hung processes.

Both of mine call `GET /health`. The liveness probe is slower and more tolerant (restart after about 30s) than readiness (removed after about 15s), because a restart is the bigger action. A common mistake is a liveness probe that checks a database: if the database goes down, every pod restarts in a loop, which makes things worse.

### How does Prometheus collect metrics?

It **pulls**: every 15 seconds it sends an HTTP GET to each target's metrics endpoint and stores the values as time series (metric name + labels + timestamp + value). It finds targets through **Kubernetes service discovery**, asking the API server for pods and nodes (which is why it needs RBAC permissions), and relabeling rules choose which ones to keep. I scrape three things: Prometheus itself, cAdvisor in the kubelet for container CPU and memory, and my app's `/metrics` endpoint, which uses the `prometheus_client` library to expose a request counter and a latency histogram.

Pull model benefits: Prometheus knows when a target is down (`up == 0`), and apps do not need to know where Prometheus is.

### How does Grafana visualise monitoring data?

Grafana stores no metrics itself. It connects to Prometheus as a **data source**, sends **PromQL** queries for the selected time range, and draws the results as panels (time series, stats). My data source and dashboard are **provisioned** from files in ConfigMaps, so they are recreated automatically and version-controlled in Git, rather than clicked together by hand.

### How do you troubleshoot a failed deployment?

I follow the same order every time:

1. `kubectl get pods`: read the STATUS (`ImagePullBackOff`, `CrashLoopBackOff`, `Pending`, `0/1`).
2. `kubectl describe pod <name>`: the Events usually say exactly what failed (image not found, insufficient CPU, probe returned 503, OOMKilled).
3. `kubectl logs <name> --previous`: the application's own error if it crashed.
4. `kubectl get endpoints <service>` if the app runs but cannot be reached: empty endpoints mean a label/selector mismatch or no ready pods.
5. Fix the YAML and `kubectl apply`, or `kubectl rollout undo` to recover immediately and investigate afterwards.

Example from my project: I deployed a non-existent image tag. The new pod went to `ImagePullBackOff`, but because of `maxUnavailable: 0` the old pods kept serving. `rollout undo` fixed it in seconds.

## Follow-up questions to be ready for

| Question | Short answer |
|---|---|
| Requests vs limits? | Requests are reserved and used for scheduling; limits are the maximum. CPU over the limit is throttled; memory over the limit is OOMKilled. |
| What is OOMKilled / exit code 137? | The kernel killed the process for exceeding its memory limit (137 = 128 + SIGKILL 9). |
| ClusterIP vs NodePort vs LoadBalancer? | Internal only / also on each node's port 30000-32767 / cloud load balancer in front. |
| Why a ConfigMap? | Configuration changes without rebuilding the image; the same image moves from dev to prod. Secrets are for sensitive values. |
| What is a namespace? | A logical partition of a cluster. I separate `monitoring` from the app. |
| How does a rolling update work? | New ReplicaSet scales up while the old one scales down, gated by readiness and `maxSurge`/`maxUnavailable`. |
| Why `rate()` in PromQL? | Counters only increase; `rate()` turns them into per-second change. |
| Why not Helm? | To learn what each object does first. Helm would be the next step to package and version these manifests. |
| Why only one gunicorn worker? | Scale with pods, not processes; keeps metrics in one process and resource limits predictable. |
| Why run as non-root? | If the app is compromised, the attacker has fewer privileges in the container. |
| What would you add next? | CI pipeline (GitHub Actions) to test and build the image, a HorizontalPodAutoscaler, Alertmanager alerts, Helm or Kustomize, an Ingress. |

## Resume-ready description

**Kubernetes-Based Application Deployment and Monitoring** | Docker, Kubernetes (Minikube), Prometheus, Grafana, Python Flask, Linux, Git

- Containerised a Python Flask web application with a slim, non-root Docker image using layer caching, and deployed it to Kubernetes (Minikube) with Deployment, Service and ConfigMap manifests.
- Configured 3 replicas with rolling updates (zero unavailable pods), readiness and liveness probes, and CPU/memory requests and limits.
- Set up Prometheus with Kubernetes service discovery and RBAC to scrape container CPU/memory (cAdvisor) and custom application metrics, and visualised them on a provisioned Grafana dashboard.
- Validated self-healing and failure handling by deleting pods, failing health checks, deploying a broken image and triggering OOMKills; diagnosed each with kubectl describe, logs and events and recovered with rollbacks.
- Documented architecture, deployment and troubleshooting steps, and added automated tests that validate the application and the consistency of the Kubernetes manifests.
