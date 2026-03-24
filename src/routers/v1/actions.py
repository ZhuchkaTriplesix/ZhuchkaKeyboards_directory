"""Business logic for `/api/v1` customer self-service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.database.models import Customer, CustomerAddress, CustomerB2BLink, CustomerConsent
from src.routers.v1.dal import (
    address_add,
    address_delete,
    address_get_for_customer,
    addresses_by_customer,
    b2b_link_add,
    b2b_link_by_customer_counterparty,
    b2b_link_delete,
    b2b_link_get_for_customer,
    b2b_links_by_customer,
    clear_other_defaults,
    consent_add,
    consent_by_customer_and_type,
    consents_active_by_customer,
    consents_all_by_customer,
    customer_by_id,
    customer_by_subject,
    customer_create,
    customer_email_taken_by_other,
    customers_search,
)
from src.routers.v1.schemas import (
    AddressCreate,
    AddressOut,
    AddressPatch,
    B2BLinkCreate,
    B2BLinkOut,
    ConsentOut,
    ConsentUpsert,
    CustomerListResponse,
    CustomerOut,
    CustomerPatch,
    MergeCustomerIn,
)


def _consent_preferred(a: CustomerConsent, b: CustomerConsent) -> CustomerConsent:
    """Prefer active over withdrawn; then newer ``granted_at``."""
    a_act = a.withdrawn_at is None
    b_act = b.withdrawn_at is None
    if a_act != b_act:
        return a if a_act else b
    if a.granted_at >= b.granted_at:
        return a
    return b


async def _dedupe_default_addresses(session: AsyncSession, customer_id: UUID) -> None:
    rows = await addresses_by_customer(session, customer_id)
    defaults = [r for r in rows if r.is_default]
    if len(defaults) <= 1:
        return
    for r in defaults[1:]:
        r.is_default = False
    await session.flush()


async def _merge_b2b_links(session: AsyncSession, source_id: UUID, into_id: UUID) -> None:
    for link in await b2b_links_by_customer(session, source_id):
        existing = await b2b_link_by_customer_counterparty(session, into_id, link.counterparty_id)
        if existing is None:
            link.customer_id = into_id
        else:
            await session.execute(delete(CustomerB2BLink).where(CustomerB2BLink.id == link.id))
    await session.flush()


async def _ensure_customer(session: AsyncSession, subject: UUID) -> Customer:
    row = await customer_by_subject(session, subject)
    if row is None:
        row = await customer_create(session, subject)
        await session.flush()
    return row


async def get_or_create_me(session: AsyncSession, subject: UUID) -> CustomerOut:
    row = await _ensure_customer(session, subject)
    return CustomerOut.model_validate(row)


async def patch_me(session: AsyncSession, subject: UUID, body: CustomerPatch) -> CustomerOut:
    row = await customer_by_subject(session, subject)
    if row is None:
        row = await customer_create(session, subject)
    data = body.model_dump(exclude_unset=True)
    if "email" in data:
        row.email = str(data["email"]) if data["email"] is not None else None
    if "display_name" in data:
        row.display_name = data["display_name"]
    if "phone" in data:
        row.phone = data["phone"]
    if "kind" in data and data["kind"] is not None:
        row.kind = data["kind"].value
    if "locale" in data:
        row.locale = data["locale"]
    if "timezone" in data:
        row.timezone = data["timezone"]
    await session.flush()
    await session.refresh(row)
    return CustomerOut.model_validate(row)


async def list_addresses(session: AsyncSession, subject: UUID) -> list[AddressOut]:
    cust = await _ensure_customer(session, subject)
    rows = await addresses_by_customer(session, cust.id)
    return [AddressOut.model_validate(r) for r in rows]


async def create_address(session: AsyncSession, subject: UUID, body: AddressCreate) -> AddressOut:
    cust = await _ensure_customer(session, subject)
    addr = CustomerAddress(
        customer_id=cust.id,
        kind=body.kind.value,
        line1=body.line1,
        line2=body.line2,
        city=body.city,
        region=body.region,
        postal_code=body.postal_code,
        country=body.country,
        is_default=body.is_default,
    )
    addr = await address_add(session, addr)
    if body.is_default:
        await clear_other_defaults(session, cust.id, addr.id)
    await session.refresh(addr)
    return AddressOut.model_validate(addr)


async def patch_address(
    session: AsyncSession, subject: UUID, address_id: UUID, body: AddressPatch
) -> AddressOut:
    cust = await _ensure_customer(session, subject)
    row = await address_get_for_customer(session, cust.id, address_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="address_not_found")
    data = body.model_dump(exclude_unset=True)
    if "kind" in data and data["kind"] is not None:
        row.kind = data["kind"].value
    if "line1" in data:
        row.line1 = data["line1"]
    if "line2" in data:
        row.line2 = data["line2"]
    if "city" in data:
        row.city = data["city"]
    if "region" in data:
        row.region = data["region"]
    if "postal_code" in data:
        row.postal_code = data["postal_code"]
    if "country" in data:
        row.country = data["country"]
    if "is_default" in data and data["is_default"] is not None:
        row.is_default = data["is_default"]
        if data["is_default"]:
            await clear_other_defaults(session, cust.id, row.id)
    await session.flush()
    await session.refresh(row)
    return AddressOut.model_validate(row)


async def delete_address(session: AsyncSession, subject: UUID, address_id: UUID) -> None:
    cust = await _ensure_customer(session, subject)
    row = await address_get_for_customer(session, cust.id, address_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="address_not_found")
    await address_delete(session, row)


async def list_consents(session: AsyncSession, subject: UUID) -> list[ConsentOut]:
    cust = await _ensure_customer(session, subject)
    rows = await consents_active_by_customer(session, cust.id)
    return [ConsentOut.model_validate(r) for r in rows]


async def upsert_consent(session: AsyncSession, subject: UUID, body: ConsentUpsert) -> ConsentOut:
    cust = await _ensure_customer(session, subject)
    ctype = body.consent_type.value
    now = datetime.now(UTC)
    row = await consent_by_customer_and_type(session, cust.id, ctype)

    if body.granted:
        assert body.document_version is not None
        ver = body.document_version.strip()
        if row is None:
            row = CustomerConsent(
                customer_id=cust.id,
                consent_type=ctype,
                document_version=ver,
                granted_at=now,
                withdrawn_at=None,
                source=body.source,
            )
            await consent_add(session, row)
        else:
            row.document_version = ver
            row.granted_at = now
            row.withdrawn_at = None
            row.source = body.source
            await session.flush()
        await session.refresh(row)
        return ConsentOut.model_validate(row)

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="consent_not_found")
    if row.withdrawn_at is not None:
        await session.refresh(row)
        return ConsentOut.model_validate(row)
    row.withdrawn_at = now
    await session.flush()
    await session.refresh(row)
    return ConsentOut.model_validate(row)


async def list_b2b_links(session: AsyncSession, subject: UUID) -> list[B2BLinkOut]:
    cust = await _ensure_customer(session, subject)
    rows = await b2b_links_by_customer(session, cust.id)
    return [B2BLinkOut.model_validate(r) for r in rows]


async def create_b2b_link(session: AsyncSession, subject: UUID, body: B2BLinkCreate) -> B2BLinkOut:
    cust = await _ensure_customer(session, subject)
    if await b2b_link_by_customer_counterparty(session, cust.id, body.counterparty_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="b2b_link_exists",
        )
    row = CustomerB2BLink(
        customer_id=cust.id,
        counterparty_id=body.counterparty_id,
        contact_role=body.contact_role.strip(),
    )
    await b2b_link_add(session, row)
    await session.refresh(row)
    return B2BLinkOut.model_validate(row)


async def delete_b2b_link(session: AsyncSession, subject: UUID, link_id: UUID) -> None:
    cust = await _ensure_customer(session, subject)
    row = await b2b_link_get_for_customer(session, cust.id, link_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="b2b_link_not_found")
    await b2b_link_delete(session, row)


async def list_customers_staff(
    session: AsyncSession,
    *,
    email_contains: str | None,
    subject: UUID | None,
    counterparty_id: UUID | None,
    limit: int,
    offset: int,
) -> CustomerListResponse:
    email_q: str | None = None
    if email_contains is not None:
        stripped = email_contains.strip()
        if stripped:
            email_q = stripped
    rows, total = await customers_search(
        session,
        email_contains=email_q,
        subject=subject,
        counterparty_id=counterparty_id,
        limit=limit,
        offset=offset,
    )
    return CustomerListResponse(
        items=[CustomerOut.model_validate(r) for r in rows],
        total=total,
    )


async def get_customer_staff(session: AsyncSession, customer_id: UUID) -> CustomerOut:
    row = await customer_by_id(session, customer_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="customer_not_found")
    return CustomerOut.model_validate(row)


async def patch_customer_staff(
    session: AsyncSession, customer_id: UUID, body: CustomerPatch
) -> CustomerOut:
    row = await customer_by_id(session, customer_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="customer_not_found")
    data = body.model_dump(exclude_unset=True)
    if "email" in data:
        if data["email"] is not None:
            new_email = str(data["email"]).strip().lower()
            current = (row.email or "").strip().lower()
            if new_email != current and await customer_email_taken_by_other(
                session, new_email, customer_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="email_already_exists",
                )
            row.email = new_email
        else:
            row.email = None
    if "display_name" in data:
        row.display_name = data["display_name"]
    if "phone" in data:
        row.phone = data["phone"]
    if "kind" in data and data["kind"] is not None:
        row.kind = data["kind"].value
    if "locale" in data:
        row.locale = data["locale"]
    if "timezone" in data:
        row.timezone = data["timezone"]
    await session.flush()
    await session.refresh(row)
    return CustomerOut.model_validate(row)


async def merge_customers_staff(
    session: AsyncSession, source_customer_id: UUID, body: MergeCustomerIn
) -> CustomerOut:
    into_id = body.into_customer_id
    if source_customer_id == into_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cannot_merge_self",
        )
    source = await customer_by_id(session, source_customer_id)
    if source is None or await customer_by_id(session, into_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="customer_not_found")

    await session.execute(
        update(CustomerAddress)
        .where(CustomerAddress.customer_id == source_customer_id)
        .values(customer_id=into_id)
    )
    await session.flush()
    await _dedupe_default_addresses(session, into_id)

    source_consents = await consents_all_by_customer(session, source_customer_id)
    for sc in source_consents:
        tc = await consent_by_customer_and_type(session, into_id, sc.consent_type)
        if tc is None:
            sc.customer_id = into_id
        else:
            keep = _consent_preferred(sc, tc)
            if keep.id == sc.id:
                await session.execute(delete(CustomerConsent).where(CustomerConsent.id == tc.id))
                sc.customer_id = into_id
            else:
                await session.execute(delete(CustomerConsent).where(CustomerConsent.id == sc.id))
    await session.flush()

    await _merge_b2b_links(session, source_customer_id, into_id)

    await session.execute(delete(Customer).where(Customer.id == source_customer_id))
    await session.flush()

    row = await customer_by_id(session, into_id)
    assert row is not None
    return CustomerOut.model_validate(row)
