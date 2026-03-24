"""Data access for customer profiles and addresses."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Customer, CustomerAddress


async def customer_by_subject(session: AsyncSession, subject: UUID) -> Customer | None:
    result = await session.execute(select(Customer).where(Customer.subject == subject))
    return result.scalar_one_or_none()


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
