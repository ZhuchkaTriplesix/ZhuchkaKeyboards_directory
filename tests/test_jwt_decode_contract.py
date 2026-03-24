"""JWT decode + RS256 (no network, no Postgres). Refs integration contract for Auth."""

from __future__ import annotations

import json
import time
import uuid
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from jwt import PyJWK
from jwt.algorithms import RSAAlgorithm

TEST_ISS = "http://127.0.0.1:8000"
TEST_AUD = "zhuchka-api"


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


def test_decode_access_token_rs256_roundtrip(monkeypatch, rsa_private):
    signing_key = _signing_key_from_private(rsa_private)
    monkeypatch.setattr("src.auth_token._jwks_client", _fake_jwks_client(signing_key))
    monkeypatch.setattr(
        "src.auth_token._auth_cfg",
        SimpleNamespace(jwks_url="http://fixture.invalid/jwks", issuer=TEST_ISS, audience=TEST_AUD),
    )

    sub = str(uuid.uuid4())
    now = int(time.time())
    claims_in = {
        "sub": sub,
        "iss": TEST_ISS,
        "aud": TEST_AUD,
        "exp": now + 3600,
        "iat": now,
        "token_use": "access",
        "scope": "profile",
    }
    token = jwt.encode(
        claims_in,
        rsa_private,
        algorithm="RS256",
        headers={"kid": "test-kid"},
    )

    from src.auth_token import decode_access_token

    out = decode_access_token(token)
    assert out["sub"] == sub
    assert out["token_use"] == "access"


def test_decode_access_token_rejects_non_access_token_use(monkeypatch, rsa_private):
    signing_key = _signing_key_from_private(rsa_private)
    monkeypatch.setattr("src.auth_token._jwks_client", _fake_jwks_client(signing_key))
    monkeypatch.setattr(
        "src.auth_token._auth_cfg",
        SimpleNamespace(jwks_url="http://fixture.invalid/jwks", issuer=TEST_ISS, audience=TEST_AUD),
    )

    sub = str(uuid.uuid4())
    now = int(time.time())
    claims_in = {
        "sub": sub,
        "iss": TEST_ISS,
        "aud": TEST_AUD,
        "exp": now + 3600,
        "iat": now,
        "token_use": "refresh",
    }
    token = jwt.encode(claims_in, rsa_private, algorithm="RS256", headers={"kid": "test-kid"})

    from src.auth_token import decode_access_token

    with pytest.raises(HTTPException) as exc:
        decode_access_token(token)
    assert exc.value.status_code == 401
