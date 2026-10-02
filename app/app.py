"""A deliberately small Flask app: the focus of this project is DevOps, not features.

Endpoints
  GET  /         homepage (shows which pod answered)
  GET  /health   used by Kubernetes readiness and liveness probes
  GET  /metrics  Prometheus scrape endpoint
  GET  /work     burns a little CPU so the Grafana graphs move (?ms=100)
  POST /fail     makes /health return 503 so you can watch the liveness probe restart the pod
"""
import time

from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from config import settings

app = Flask(__name__)

REQUESTS = Counter(
    "flask_http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
LATENCY = Histogram(
    "flask_http_request_duration_seconds", "HTTP request latency in seconds", ["endpoint"]
)

MAX_WORK_MS = 1000

# Per-process flag. Flipped by POST /fail to simulate an app that is "running but broken".
_state = {"healthy": True}

HOMEPAGE = """<!doctype html>
<html><head><title>{name}</title>
<style>body{{font-family:sans-serif;max-width:640px;margin:60px auto;line-height:1.6}}
code{{background:#f3f3f3;padding:2px 6px;border-radius:4px}}</style></head>
<body>
<h1>Hello from {name} &#128075;</h1>
<p>Served by pod <code>{hostname}</code></p>
<p>Version <code>{version}</code> &middot; environment <code>{env}</code></p>
<p>Refresh the page: when the request goes through the Kubernetes Service, a different pod may answer.</p>
<p>Try <a href="/health">/health</a> and <a href="/metrics">/metrics</a>.</p>
</body></html>"""


@app.before_request
def _start_timer():
    g.start = time.perf_counter()


@app.after_request
def _record_metrics(response):
    # Use the route pattern (e.g. "/work"), not the raw URL, so query strings or
    # random paths cannot create unlimited label values (high cardinality).
    endpoint = request.url_rule.rule if request.url_rule else "unmatched"
    if endpoint != "/metrics":
        REQUESTS.labels(request.method, endpoint, response.status_code).inc()
        LATENCY.labels(endpoint).observe(time.perf_counter() - g.start)
    return response


@app.get("/")
def home():
    return HOMEPAGE.format(
        name=settings.app_name,
        hostname=settings.hostname,
        version=settings.app_version,
        env=settings.app_env,
    )


@app.get("/health")
def health():
    if _state["healthy"]:
        return jsonify(status="ok", pod=settings.hostname)
    return jsonify(status="unhealthy", pod=settings.hostname), 503


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.get("/work")
def work():
    ms = min(request.args.get("ms", default=100, type=int), MAX_WORK_MS)
    deadline = time.perf_counter() + ms / 1000
    count = 0
    while time.perf_counter() < deadline:
        count += 1
    return jsonify(busy_ms=ms, iterations=count, pod=settings.hostname)


@app.post("/fail")
def fail():
    _state["healthy"] = False
    return jsonify(status="health check will now fail", pod=settings.hostname)


if __name__ == "__main__":
    # Local development only. In the container gunicorn runs the app (see gunicorn.conf.py).
    app.run(host="0.0.0.0", port=settings.port, debug=True)
