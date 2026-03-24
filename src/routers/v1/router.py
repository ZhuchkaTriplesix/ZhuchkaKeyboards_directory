"""Customer self-service API (Bearer access token)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from src.database.dependencies import DbSession
from src.routers.v1 import actions
from src.routers.v1.deps import current_subject, staff_claims
from src.routers.v1.schemas import (
    AddressCreate,
    AddressOut,
    AddressPatch,
    ConsentOut,
    ConsentUpsert,
    CustomerListResponse,
    CustomerOut,
    CustomerPatch,
)

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


@router.get("/me/addresses", response_model=list[AddressOut])
async def list_addresses(
    session: DbSession, subject: UUID = Depends(current_subject)
) -> list[AddressOut]:
    """List saved addresses for the current customer."""
    return await actions.list_addresses(session, subject)


@router.post("/me/addresses", response_model=AddressOut)
async def create_address(
    session: DbSession,
    body: AddressCreate,
    subject: UUID = Depends(current_subject),
) -> AddressOut:
    """Create a billing or shipping address."""
    return await actions.create_address(session, subject, body)


@router.patch("/me/addresses/{address_id}", response_model=AddressOut)
async def patch_address(
    session: DbSession,
    address_id: UUID,
    body: AddressPatch,
    subject: UUID = Depends(current_subject),
) -> AddressOut:
    """Update an address belonging to the current customer."""
    return await actions.patch_address(session, subject, address_id, body)


@router.delete("/me/addresses/{address_id}", status_code=204)
async def delete_address(
    session: DbSession,
    address_id: UUID,
    subject: UUID = Depends(current_subject),
) -> Response:
    """Delete an address. Order-level checks are out of scope here."""
    await actions.delete_address(session, subject, address_id)
    return Response(status_code=204)


@router.get("/me/consents", response_model=list[ConsentOut])
async def list_consents(
    session: DbSession, subject: UUID = Depends(current_subject)
) -> list[ConsentOut]:
    """Active consents only (``withdrawn_at`` is null)."""
    return await actions.list_consents(session, subject)


@router.post("/me/consents", response_model=ConsentOut)
async def upsert_consent(
    session: DbSession,
    body: ConsentUpsert,
    subject: UUID = Depends(current_subject),
) -> ConsentOut:
    """Grant or re-grant a consent for a document version, or withdraw (``granted=false``)."""
    return await actions.upsert_consent(session, subject, body)


@router.get("/customers", response_model=CustomerListResponse)
async def list_customers_staff(
    session: DbSession,
    _claims: dict = Depends(staff_claims),
    email: str | None = Query(
        None,
        description="Case-insensitive substring match on stored email (if set)",
    ),
    subject: UUID | None = Query(None, description="Exact Auth subject (user id)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> CustomerListResponse:
    """Operational list (requires JWT with ``admin`` scope)."""
    return await actions.list_customers_staff(
        session,
        email_contains=email,
        subject=subject,
        limit=limit,
        offset=offset,
    )


@router.get("/customers/{customer_id}", response_model=CustomerOut)
async def get_customer_staff(
    session: DbSession,
    customer_id: UUID,
    _claims: dict = Depends(staff_claims),
) -> CustomerOut:
    """Operational customer card (requires JWT with ``admin`` scope)."""
    return await actions.get_customer_staff(session, customer_id)


@router.patch("/customers/{customer_id}", response_model=CustomerOut)
async def patch_customer_staff(
    session: DbSession,
    customer_id: UUID,
    body: CustomerPatch,
    _claims: dict = Depends(staff_claims),
) -> CustomerOut:
    """Operational profile update (requires JWT with ``admin`` scope)."""
    return await actions.patch_customer_staff(session, customer_id, body)
