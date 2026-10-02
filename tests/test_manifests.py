"""Offline checks that the Kubernetes and monitoring files agree with each other.

These catch the classic "selector does not match labels" mistakes without needing a cluster.
"""
import json
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parent.parent


def load_docs(folder):
    docs = []
    for path in sorted((ROOT / folder).glob("*.yaml")):
        docs += [d for d in yaml.safe_load_all(path.read_text()) if d]
    return docs


def find(docs, kind, name):
    return next(d for d in docs if d["kind"] == kind and d["metadata"]["name"] == name)


APP = load_docs("k8s")
MON = load_docs("monitoring")


def test_deployment_selector_matches_pod_labels():
    for dep in [d for d in APP + MON if d["kind"] == "Deployment"]:
        selector = dep["spec"]["selector"]["matchLabels"]
        labels = dep["spec"]["template"]["metadata"]["labels"]
        assert selector.items() <= labels.items(), dep["metadata"]["name"]


def test_every_service_selects_a_deployment_and_a_named_port():
    deployments = [d for d in APP + MON if d["kind"] == "Deployment"]
    for svc in [d for d in APP + MON if d["kind"] == "Service"]:
        selector = svc["spec"]["selector"]
        matches = [
            d for d in deployments
            if selector.items() <= d["spec"]["template"]["metadata"]["labels"].items()
        ]
        assert matches, f"Service {svc['metadata']['name']} selects no pods"
        port_names = {p["name"] for c in matches[0]["spec"]["template"]["spec"]["containers"] for p in c["ports"]}
        for port in svc["spec"]["ports"]:
            assert port["targetPort"] in port_names


def test_probes_share_one_health_check():
    container = find(APP, "Deployment", "flask-app")["spec"]["template"]["spec"]["containers"][0]
    assert container["readinessProbe"]["httpGet"] == container["livenessProbe"]["httpGet"]
    assert container["resources"]["requests"] and container["resources"]["limits"]


def test_prometheus_config_is_valid_yaml_with_app_job():
    config = yaml.safe_load(find(MON, "ConfigMap", "prometheus-config")["data"]["prometheus.yml"])
    assert "app-pods" in {job["job_name"] for job in config["scrape_configs"]}


def test_dashboard_uses_provisioned_datasource():
    provisioning = find(MON, "ConfigMap", "grafana-provisioning")["data"]
    uid = yaml.safe_load(provisioning["datasources.yaml"])["datasources"][0]["uid"]
    dashboard = json.loads((ROOT / "monitoring/dashboards/flask-app.json").read_text())
    assert {p["datasource"]["uid"] for p in dashboard["panels"]} == {uid}
