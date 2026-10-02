import pytest

import app as app_module


@pytest.fixture
def client():
    app_module._state["healthy"] = True
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client


def test_homepage_shows_app_name(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"flask-app" in response.data


def test_health_is_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_fail_makes_health_return_503(client):
    client.post("/fail")
    assert client.get("/health").status_code == 503


def test_metrics_counts_requests(client):
    client.get("/health")
    body = client.get("/metrics").get_data(as_text=True)
    assert 'flask_http_requests_total{endpoint="/health",method="GET",status="200"}' in body


def test_work_is_capped(client):
    response = client.get("/work?ms=999999")
    assert response.get_json()["busy_ms"] == app_module.MAX_WORK_MS
