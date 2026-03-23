"""Smoke tests for public routes (no database required for liveness)."""

from starlette.testclient import TestClient

from src.configuration.app import App


def test_health_live():
    with TestClient(App().app) as client:
        r = client.get("/health/live")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
