# Kubernetes-Based Application Deployment and Monitoring

A Python Flask application containerised with **Docker**, deployed on **Kubernetes (Minikube)** with replicas, health probes and resource limits, and monitored with **Prometheus** and **Grafana**.

The application is deliberately simple. The point of the project is the DevOps work around it: packaging, orchestration, self-healing, observability and troubleshooting.

![Architecture](docs/architecture.svg)

## Features

- Flask app with `/` (shows which pod answered), `/health`, `/metrics`, plus `/work` and `/fail` for demos
- Slim, non-root Docker image with cached dependency layers
- Kubernetes Deployment with **3 replicas** and a zero-downtime rolling update strategy
- **Readiness and liveness probes** sharing one health check definition
- **CPU and memory requests and limits**
- NodePort **Service** load-balancing across the replicas, plus a ConfigMap for configuration
- **Prometheus** (plain YAML, no Helm) with Kubernetes service discovery: container CPU/memory from cAdvisor and app metrics from `/metrics`
- **Grafana** with an auto-provisioned data source and dashboard (CPU, memory, requests/s, p95 latency, healthy pods)
- Failure experiments: pod deletion, failing health check, bad release, OOMKill, CPU throttling
- Tests for both the app and the consistency of the Kubernetes manifests

## Tech stack

Linux, Python Flask, Gunicorn, Docker, Kubernetes, Minikube, Kubernetes YAML, Prometheus, Grafana, Git and GitHub.

## Repository structure

```
.
├── app/                      Flask application
│   ├── app.py                routes + Prometheus metrics
│   ├── config.py             single source of settings (env vars)
│   ├── gunicorn.conf.py      production server settings
│   └── requirements.txt
├── k8s/                      application manifests
│   ├── configmap.yaml
│   ├── deployment.yaml       replicas, probes, resources
│   └── service.yaml          NodePort 30080
├── monitoring/               monitoring manifests (applied in numeric order)
│   ├── 00-namespace.yaml
│   ├── 10-prometheus.yaml    RBAC, scrape config, deployment, service
│   ├── 20-grafana.yaml       provisioning, deployment, service
│   └── dashboards/flask-app.json
├── scripts/
│   ├── deploy.sh             build + load image + deploy everything
│   ├── load.sh               generate traffic inside the cluster
│   ├── teardown.sh           remove everything
│   └── build_pdf.py          builds the PDFs from docs/
├── tests/                    pytest: app + manifest checks
├── docs/                     guide, troubleshooting, interview prep, diagram
├── Dockerfile
└── README.md
```

## Quick start

Prerequisites: Docker Desktop (WSL2 on Windows), Minikube, kubectl, Git Bash on Windows. See [Phase 1 of the guide](docs/guide.md#phase-1---architecture-and-prerequisites).

```bash
./scripts/deploy.sh
```

This starts Minikube, builds the image, loads it into the cluster, and deploys the app, Prometheus and Grafana. Then open each one in its own terminal (each command keeps a tunnel open):

```bash
minikube service flask-app-service
minikube service prometheus -n monitoring
minikube service grafana -n monitoring
```

Grafana login: `admin` / `admin`, then open **Dashboards > Flask App on Kubernetes**. Generate traffic with `./scripts/load.sh`, and remove everything with `./scripts/teardown.sh`.

Run the tests without a cluster:

```bash
python -m venv .venv && source .venv/Scripts/activate   # Linux/macOS: .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest
```

## Documentation

| Document | Contents |
|---|---|
| [Build guide](docs/guide.md) | All 10 phases step by step. Every command with what, why, where, expected output and common errors |
| [Troubleshooting](docs/troubleshooting.md) | The get/describe/logs/events/exec method and an error catalogue |
| [Interview prep](docs/interview-prep.md) | Concept answers, follow-up questions and a resume-ready description |
| [Hinglish guide](docs/hinglish/) | Everything from the basics (networking, Linux, Docker, Kubernetes, monitoring) to interview prep, in Hinglish |
| `docs/k8s-flask-monitoring-guide.pdf` | English guide + troubleshooting + interview prep + source code in one PDF |
| `docs/k8s-flask-monitoring-guide-hinglish.pdf` | The Hinglish guide + source code in one PDF |

Both PDFs are generated from these Markdown files with `python scripts/build_pdf.py`.

## Failure experiments

| Experiment | What you see | Concept |
|---|---|---|
| `kubectl delete pod <pod>` | A replacement pod appears within seconds | ReplicaSet reconciliation |
| `POST /fail` on one pod | Pod becomes `0/1`, then restarts | Readiness vs liveness |
| `kubectl set image ... :9.9.9` | New pod `ImagePullBackOff`, old pods keep serving | Rolling update safety, `rollout undo` |
| Memory limit 16Mi | `OOMKilled`, exit code 137 | Memory limits |
| `./scripts/load.sh 500 6` | CPU flat at the limit, latency up, no restarts | CPU throttling |

Details are in [Phase 9 of the guide](docs/guide.md#phase-9---testing-and-troubleshooting).

## Screenshots

Captured after running the project locally (see [Phase 8](docs/guide.md#phase-8---the-grafana-dashboard)):

- [Grafana dashboard](docs/screenshots/grafana-dashboard.png)
- [Prometheus targets](docs/screenshots/prometheus-targets.png)
- [Running pods](docs/screenshots/pods-running.png)
- [Self-healing test](docs/screenshots/self-healing.png)

## What I learned

How Kubernetes reconciles desired and actual state, why readiness and liveness probes are different, how requests and limits affect scheduling, throttling and OOM kills, how Prometheus discovers and pulls metrics, and a repeatable method for debugging a failed deployment. See [interview prep](docs/interview-prep.md).

## Possible next steps

GitHub Actions CI to test and build the image, HorizontalPodAutoscaler, Alertmanager alerts, Ingress, and packaging the manifests with Helm or Kustomize.
