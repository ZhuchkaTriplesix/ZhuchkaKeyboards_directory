"""Bearer JWT → Auth ``sub`` (UUID)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from src.auth_token import decode_access_token, subject_uuid

_http_bearer = HTTPBearer(auto_error=False)


async def bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_http_bearer),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing_bearer_token",
        )
    return credentials.credentials


async def current_subject(token: str = Depends(bearer_token)) -> UUID:
    claims = decode_access_token(token)
    return subject_uuid(claims)


def _scope_set(claims: dict[str, Any]) -> set[str]:
    raw = claims.get("scope")
    if not raw:
        return set()
    return {p for p in str(raw).split() if p}


def _has_staff_read(scopes: set[str]) -> bool:
    """Read staff routes: ``admin``, ``support.read``, or ``support.write``."""
    return "admin" in scopes or "support.read" in scopes or "support.write" in scopes


def _has_staff_write(scopes: set[str]) -> bool:
    """Write staff routes: ``admin`` or ``support.write``."""
    return "admin" in scopes or "support.write" in scopes


async def staff_read_claims(token: str = Depends(bearer_token)) -> dict[str, Any]:
    """List/get customers: ``support.read`` or ``support.write`` or ``admin`` in JWT ``scope``."""
    claims = decode_access_token(token)
    if not _has_staff_read(_scope_set(claims)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="insufficient_scope",
        )
    return claims


async def staff_write_claims(token: str = Depends(bearer_token)) -> dict[str, Any]:
    """Patch/merge customers: ``support.write`` or ``admin`` in JWT ``scope``."""
    claims = decode_access_token(token)
    if not _has_staff_write(_scope_set(claims)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="insufficient_scope",
        )
    return claims
