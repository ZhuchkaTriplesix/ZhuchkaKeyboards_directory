"""API smoke with Bearer JWT when Postgres is reachable (CI or local dev)."""

from __future__ import annotations

import json
import time
import uuid
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import PyJWK
from jwt.algorithms import RSAAlgorithm
from sqlalchemy import text
from starlette.testclient import TestClient

ISS = "http://127.0.0.1:8000"
AUD = "zhuchka-api"


@pytest.fixture(scope="session")
def postgres_reachable() -> None:
    """Skip integration tests if the app cannot open a DB connection."""
    import asyncio

    from src.database.core import engine

    async def ping() -> None:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    try:
        asyncio.run(ping())
    except Exception as exc:
        pytest.skip(f"Postgres not reachable for integration tests: {exc}")


@pytest.fixture
def rsa_private():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())


def _signing_key_from_private(rsa_private):
    pub = rsa_private.public_key()
    jwk_dict = RSAAlgorithm.to_jwk(pub, as_dict=True)
    jwk_dict["kid"] = "test-kid"
    jwk_dict["use"] = "sig"
    jwk_dict["alg"] = "RS256"
    return PyJWK.from_json(json.dumps(jwk_dict))


def _fake_jwks_client(signing_key: PyJWK):
    class Fake:
        def get_signing_key_from_jwt(self, token):  # noqa: ARG002
            return signing_key

    return Fake()


def _access_token(rsa_private, subject: str) -> str:
    now = int(time.time())
    claims = {
        "sub": subject,
        "iss": ISS,
        "aud": AUD,
        "exp": now + 3600,
        "iat": now,
        "token_use": "access",
        "scope": "profile",
    }
    return jwt.encode(claims, rsa_private, algorithm="RS256", headers={"kid": "test-kid"})


@pytest.mark.integration
@pytest.mark.usefixtures("postgres_reachable")
def test_get_me_lazy_provision(monkeypatch, rsa_private) -> None:
    """GET /api/v1/me returns 200 and creates a profile row keyed by JWT sub."""
    signing_key = _signing_key_from_private(rsa_private)
    monkeypatch.setattr("src.auth_token._jwks_client", _fake_jwks_client(signing_key))
    monkeypatch.setattr(
        "src.auth_token._auth_cfg",
        SimpleNamespace(jwks_url="http://fixture.invalid/jwks", issuer=ISS, audience=AUD),
    )

    sub = str(uuid.uuid4())
    token = _access_token(rsa_private, sub)

    from src.main import app

    with TestClient(app) as client:
        r = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 200
    data = r.json()
    assert data["subject"] == sub

    # Second call is idempotent (same row)
    with TestClient(app) as client:
        r2 = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.json()["id"] == data["id"]
