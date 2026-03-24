"""Bearer JWT → Auth ``sub`` (UUID)."""

from __future__ import annotations

from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth_token import decode_access_token, subject_uuid

_http_bearer = HTTPBearer(auto_error=False)


async def bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_http_bearer),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        from fastapi import HTTPException
        from starlette import status

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing_bearer_token",
        )
    return credentials.credentials


async def current_subject(token: str = Depends(bearer_token)) -> UUID:
    claims = decode_access_token(token)
    return subject_uuid(claims)
