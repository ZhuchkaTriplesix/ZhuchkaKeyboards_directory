"""OpenAPI and docs routes registered on ``src.main:app`` require HTTP Basic auth."""

from starlette.testclient import TestClient

from src.main import app


def test_openapi_json_returns_401_without_credentials():
    with TestClient(app) as client:
        r = client.get("/api/openapi.json")
    assert r.status_code == 401


def test_openapi_json_returns_schema_with_valid_basic_auth():
    with TestClient(app) as client:
        r = client.get("/api/openapi.json", auth=("USERNAME", "PASSWORD"))
    assert r.status_code == 200
    body = r.json()
    assert body.get("openapi") is not None
    assert "paths" in body
