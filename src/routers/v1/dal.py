"""Data access for customer profiles."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Customer


async def customer_by_subject(session: AsyncSession, subject: UUID) -> Customer | None:
    result = await session.execute(select(Customer).where(Customer.subject == subject))
    return result.scalar_one_or_none()


async def customer_create(session: AsyncSession, subject: UUID) -> Customer:
    row = Customer(subject=subject)
    session.add(row)
    await session.flush()
    return row
