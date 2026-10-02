#!/usr/bin/env bash
# Remove everything deploy.sh created (the Minikube cluster itself is kept).
set -euo pipefail
cd "$(dirname "$0")/.."

kubectl delete -f k8s/ --ignore-not-found
kubectl delete -f monitoring/ --ignore-not-found   # deleting the namespace also removes grafana-dashboards
echo "Removed. Run 'minikube stop' to pause the cluster or 'minikube delete' to remove it."
