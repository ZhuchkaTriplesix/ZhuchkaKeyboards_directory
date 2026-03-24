"""Metrics and request correlation (issue #7)."""

from starlette.testclient import TestClient

from src.configuration.app import App
from src.main import app as main_app


def test_metrics_prometheus_text():
    with TestClient(App().app) as client:
        r = client.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("content-type", "")
    assert b"python_info" in r.content or b"# HELP" in r.content


def test_x_request_id_echo_and_propagate():
    with TestClient(main_app) as client:
        r = client.get("/health/live", headers={"X-Request-ID": "trace-from-gateway-1"})
    assert r.status_code == 200
    assert r.headers.get("X-Request-ID") == "trace-from-gateway-1"


def test_x_request_id_generated_when_absent():
    with TestClient(main_app) as client:
        r = client.get("/health/live")
    assert r.status_code == 200
    assert r.headers.get("X-Request-ID")
    assert len(r.headers["X-Request-ID"]) >= 8
