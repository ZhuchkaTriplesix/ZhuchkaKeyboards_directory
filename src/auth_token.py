"""Validate Auth service JWTs (RS256) using JWKS."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import jwt
from fastapi import HTTPException
from jwt import PyJWKClient
from starlette import status

from src.config import AuthCfg

_auth_cfg = AuthCfg()
_jwks_client: PyJWKClient | None = None


def _client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(_auth_cfg.jwks_url)
    return _jwks_client


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode Bearer access token; raises HTTPException 401 on failure."""
    try:
        signing_key = _client().get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=_auth_cfg.audience,
            issuer=_auth_cfg.issuer.rstrip("/"),
            options={"require": ["exp", "sub", "iss", "aud"]},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_token",
        ) from None
    if claims.get("token_use") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_token_use",
        )
    return claims


def subject_uuid(claims: dict[str, Any]) -> UUID:
    try:
        return UUID(str(claims["sub"]))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_sub",
        ) from None
