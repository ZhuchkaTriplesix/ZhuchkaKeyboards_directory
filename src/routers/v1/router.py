"""Customer self-service API (Bearer access token)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from src.database.dependencies import DbSession
from src.routers.v1 import actions
from src.routers.v1.deps import current_subject
from src.routers.v1.schemas import CustomerOut, CustomerPatch

router = APIRouter()


@router.get("/me", response_model=CustomerOut)
async def get_me(session: DbSession, subject: UUID = Depends(current_subject)) -> CustomerOut:
    """Return the current customer profile; create a stub row on first access (lazy provisioning)."""
    return await actions.get_or_create_me(session, subject)


@router.patch("/me", response_model=CustomerOut)
async def patch_me(
    session: DbSession,
    body: CustomerPatch,
    subject: UUID = Depends(current_subject),
) -> CustomerOut:
    """Update allowed profile fields for the authenticated subject."""
    return await actions.patch_me(session, subject, body)
