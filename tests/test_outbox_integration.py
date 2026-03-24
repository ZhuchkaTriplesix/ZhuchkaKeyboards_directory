"""Outbox rows written with domain changes when Postgres is up (CI or local)."""

from __future__ import annotations

import asyncio
import uuid
from types import SimpleNamespace

import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import text
from starlette.testclient import TestClient

from src.database.core import async_session_maker
from src.events.schemas import DIRECTORY_CUSTOMER_CREATED
from tests.test_api_v1_me_integration import (
    AUD,
    ISS,
    _access_token,
    _fake_jwks_client,
    _signing_key_from_private,
)


@pytest.fixture
def rsa_private():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())


async def _count_outbox_created_for_subject(subject: str) -> int:
    async with async_session_maker() as session:
        r = await session.execute(
            text(
                "SELECT COUNT(*) FROM outbox_event "
                "WHERE event_type = :et AND payload->>'subject' = :sub"
            ),
            {"et": DIRECTORY_CUSTOMER_CREATED, "sub": subject},
        )
        return int(r.scalar_one())


@pytest.mark.integration
@pytest.mark.usefixtures("postgres_reachable")
def test_get_me_writes_outbox_customer_created(monkeypatch, rsa_private) -> None:
    signing_key = _signing_key_from_private(rsa_private)
    monkeypatch.setattr("src.auth_token._jwks_client", _fake_jwks_client(signing_key))
    monkeypatch.setattr(
        "src.auth_token._auth_cfg",
        SimpleNamespace(jwks_url="http://fixture.invalid/jwks", issuer=ISS, audience=AUD),
    )

    sub = str(uuid.uuid4())
    token = _access_token(rsa_private, sub)

    from src.main import app

    assert asyncio.run(_count_outbox_created_for_subject(sub)) == 0

    with TestClient(app) as client:
        r = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 200
    assert asyncio.run(_count_outbox_created_for_subject(sub)) == 1

    payload = asyncio.run(_fetch_latest_payload_dict(sub))
    assert payload["subject"] == sub
    assert "customer_id" in payload


async def _fetch_latest_payload_dict(subject: str) -> dict:
    async with async_session_maker() as session:
        r = await session.execute(
            text(
                "SELECT payload FROM outbox_event "
                "WHERE event_type = :et AND payload->>'subject' = :sub "
                "ORDER BY created_at DESC LIMIT 1"
            ),
            {"et": DIRECTORY_CUSTOMER_CREATED, "sub": subject},
        )
        row = r.scalar_one()
    assert isinstance(row, dict)
    return row
