#!/usr/bin/env bash
# Build the image and deploy the app + monitoring to Minikube in one go.
# Run from Git Bash (Windows), WSL or any Linux/macOS terminal:  ./scripts/deploy.sh
#
# DRY: the image name and tag are read from k8s/deployment.yaml, so the version
# is written in exactly one place.
set -euo pipefail
cd "$(dirname "$0")/.."

IMAGE=$(awk '$1 == "image:" {print $2; exit}' k8s/deployment.yaml)
VERSION=${IMAGE##*:}

step() { printf '\n==> %s\n' "$*"; }

step "Starting Minikube (skipped if it is already running)"
minikube status >/dev/null 2>&1 || minikube start --driver=docker --cpus=2 --memory=4096
minikube addons enable metrics-server >/dev/null   # enables `kubectl top`

step "Building $IMAGE"
docker build --build-arg APP_VERSION="$VERSION" -t "$IMAGE" .

step "Loading $IMAGE into Minikube"
minikube image load "$IMAGE"

step "Deploying the application"
kubectl apply -f k8s/

step "Deploying Prometheus and Grafana"
kubectl apply -f monitoring/
# Generate the dashboard ConfigMap from the JSON file (create-or-update).
kubectl create configmap grafana-dashboards -n monitoring \
  --from-file=monitoring/dashboards/ --dry-run=client -o yaml | kubectl apply -f -

step "Waiting for everything to become ready"
kubectl rollout status deployment/flask-app --timeout=120s
kubectl rollout status deployment/prometheus -n monitoring --timeout=180s
kubectl rollout status deployment/grafana -n monitoring --timeout=180s

step "Done. Open the services (each command keeps a tunnel open; use a separate terminal):"
cat <<'EOF'
  minikube service flask-app-service
  minikube service prometheus -n monitoring
  minikube service grafana -n monitoring     # login admin / admin
EOF
