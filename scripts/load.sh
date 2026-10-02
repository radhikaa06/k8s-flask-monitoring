#!/usr/bin/env bash
# Generate traffic from INSIDE the cluster so the Grafana graphs move.
# Requests go through the Service, so you can watch the load spread across pods.
#
# Usage: ./scripts/load.sh [busy-ms-per-request] [parallel-clients]
#   ./scripts/load.sh          light load (50 ms, 1 client)
#   ./scripts/load.sh 500 6    heavy load: pods hit their CPU limit
# Stop with Ctrl+C (the pod is deleted automatically).
set -euo pipefail

MS=${1:-50}
CLIENTS=${2:-1}
# winpty is needed for interactive kubectl in Git Bash on Windows.
TTY=$(command -v winpty >/dev/null 2>&1 && echo winpty || true)

$TTY kubectl run load-generator --rm -it --restart=Never --image=busybox:1.36 -- /bin/sh -c "
  for i in \$(seq $CLIENTS); do
    while true; do wget -q -O /dev/null 'http://flask-app-service/work?ms=$MS'; done &
  done
  echo 'Sending load with $CLIENTS client(s), $MS ms per request. Ctrl+C to stop.'
  wait"
