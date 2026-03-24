"""Per-request id: ``X-Request-ID`` header or generated UUID; context for logging."""

from __future__ import annotations

import re
from contextvars import ContextVar
from typing import Final
from uuid import uuid4

from starlette.requests import Request

REQUEST_ID_HEADER: Final[str] = "X-Request-ID"
_MAX_LEN: Final[int] = 128
_request_id_ctx_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return _request_id_ctx_var.get()


def _normalize_request_id(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.strip()
    if not s or len(s) > _MAX_LEN:
        return None
    if not re.match(r"^[a-zA-Z0-9._\-]{1,128}$", s):
        return None
    return s


async def request_id_middleware(request: Request, call_next):
    """Outermost HTTP middleware: set request id on request, context, and response."""
    raw = request.headers.get("x-request-id") or request.headers.get("X-Request-ID")
    rid = _normalize_request_id(raw) or str(uuid4())
    token = _request_id_ctx_var.set(rid)
    request.state.request_id = rid
    try:
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = rid
        return response
    finally:
        _request_id_ctx_var.reset(token)
