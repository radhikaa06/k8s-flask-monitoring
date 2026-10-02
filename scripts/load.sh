#!/usr/bin/env bash
# Generate traffic from INSIDE the cluster so the Grafana graphs move.
# Requests go through the Service, so you can watch the load spread across pods.
# Stop with Ctrl+C. Usage: ./scripts/load.sh [busy-ms-per-request]
set -euo pipefail

MS=${1:-50}
# winpty is needed for interactive kubectl in Git Bash on Windows.
TTY=$(command -v winpty >/dev/null 2>&1 && echo winpty || true)

$TTY kubectl run load-generator --rm -it --restart=Never --image=busybox:1.36 -- \
  /bin/sh -c "while true; do wget -q -O /dev/null http://flask-app-service/work?ms=$MS; done"
