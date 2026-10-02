"""Production web server settings. The port comes from config.py (DRY)."""
from config import settings

bind = f"0.0.0.0:{settings.port}"

# One process per container: in Kubernetes we scale by adding pods (replicas),
# not workers. It also keeps the Prometheus counters in a single process.
workers = 1
threads = 4

accesslog = "-"  # log requests to stdout so `kubectl logs` shows them
