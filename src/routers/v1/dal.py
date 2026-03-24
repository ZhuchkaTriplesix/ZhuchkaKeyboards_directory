"""Data access for customer profiles and addresses."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Customer, CustomerAddress, CustomerConsent


async def customer_by_subject(session: AsyncSession, subject: UUID) -> Customer | None:
    result = await session.execute(select(Customer).where(Customer.subject == subject))
    return result.scalar_one_or_none()


async def customer_by_id(session: AsyncSession, customer_id: UUID) -> Customer | None:
    result = await session.execute(select(Customer).where(Customer.id == customer_id))
    return result.scalar_one_or_none()


async def customers_search(
    session: AsyncSession,
    *,
    email_contains: str | None,
    subject: UUID | None,
    limit: int,
    offset: int,
) -> tuple[list[Customer], int]:
    stmt = select(Customer).order_by(Customer.created_at.desc())
    count_stmt = select(func.count()).select_from(Customer)
    if email_contains:
        pattern = f"%{email_contains.strip()}%"
        cond = Customer.email.ilike(pattern)
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    if subject is not None:
        stmt = stmt.where(Customer.subject == subject)
        count_stmt = count_stmt.where(Customer.subject == subject)
    total = (await session.execute(count_stmt)).scalar_one()
    stmt = stmt.limit(limit).offset(offset)
    rows = (await session.execute(stmt)).scalars().all()
    return list(rows), int(total)


async def customer_create(session: AsyncSession, subject: UUID) -> Customer:
    row = Customer(subject=subject)
    session.add(row)
    await session.flush()
    return row


async def addresses_by_customer(session: AsyncSession, customer_id: UUID) -> list[CustomerAddress]:
    result = await session.execute(
        select(CustomerAddress)
        .where(CustomerAddress.customer_id == customer_id)
        .order_by(CustomerAddress.created_at.asc())
    )
    return list(result.scalars().all())


async def address_get_for_customer(
    session: AsyncSession, customer_id: UUID, address_id: UUID
) -> CustomerAddress | None:
    result = await session.execute(
        select(CustomerAddress).where(
            CustomerAddress.id == address_id,
            CustomerAddress.customer_id == customer_id,
        )
    )
    return result.scalar_one_or_none()


async def address_add(session: AsyncSession, row: CustomerAddress) -> CustomerAddress:
    session.add(row)
    await session.flush()
    return row


async def address_delete(session: AsyncSession, row: CustomerAddress) -> None:
    await session.execute(delete(CustomerAddress).where(CustomerAddress.id == row.id))
    await session.flush()


async def clear_other_defaults(session: AsyncSession, customer_id: UUID, keep_id: UUID) -> None:
    await session.execute(
        update(CustomerAddress)
        .where(
            CustomerAddress.customer_id == customer_id,
            CustomerAddress.id != keep_id,
        )
        .values(is_default=False)
    )


async def consents_active_by_customer(
    session: AsyncSession, customer_id: UUID
) -> list[CustomerConsent]:
    result = await session.execute(
        select(CustomerConsent)
        .where(
            CustomerConsent.customer_id == customer_id,
            CustomerConsent.withdrawn_at.is_(None),
        )
        .order_by(CustomerConsent.consent_type.asc())
    )
    return list(result.scalars().all())


async def consent_by_customer_and_type(
    session: AsyncSession, customer_id: UUID, consent_type: str
) -> CustomerConsent | None:
    result = await session.execute(
        select(CustomerConsent).where(
            CustomerConsent.customer_id == customer_id,
            CustomerConsent.consent_type == consent_type,
        )
    )
    return result.scalar_one_or_none()


async def consent_add(session: AsyncSession, row: CustomerConsent) -> CustomerConsent:
    session.add(row)
    await session.flush()
    return row
