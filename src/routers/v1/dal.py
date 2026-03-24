"""Data access for customer profiles and addresses."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Customer, CustomerAddress, CustomerB2BLink, CustomerConsent


async def customer_by_subject(session: AsyncSession, subject: UUID) -> Customer | None:
    result = await session.execute(select(Customer).where(Customer.subject == subject))
    return result.scalar_one_or_none()


async def customer_by_id(session: AsyncSession, customer_id: UUID) -> Customer | None:
    result = await session.execute(select(Customer).where(Customer.id == customer_id))
    return result.scalar_one_or_none()


async def customer_email_taken_by_other(
    session: AsyncSession, email: str, exclude_customer_id: UUID
) -> bool:
    """Case-insensitive match on stored email."""
    result = await session.execute(
        select(Customer.id).where(
            func.lower(Customer.email) == email.lower(),
            Customer.id != exclude_customer_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def customers_search(
    session: AsyncSession,
    *,
    email_contains: str | None,
    subject: UUID | None,
    counterparty_id: UUID | None,
    limit: int,
    offset: int,
) -> tuple[list[Customer], int]:
    join_cp = counterparty_id is not None
    stmt = select(Customer)
    if join_cp:
        stmt = stmt.join(
            CustomerB2BLink,
            CustomerB2BLink.customer_id == Customer.id,
        ).where(CustomerB2BLink.counterparty_id == counterparty_id)
        count_stmt = (
            select(func.count(func.distinct(Customer.id)))
            .select_from(Customer)
            .join(CustomerB2BLink, CustomerB2BLink.customer_id == Customer.id)
            .where(CustomerB2BLink.counterparty_id == counterparty_id)
        )
    else:
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
    stmt = stmt.order_by(Customer.created_at.desc())
    if join_cp:
        stmt = stmt.distinct()
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


async def consents_all_by_customer(
    session: AsyncSession, customer_id: UUID
) -> list[CustomerConsent]:
    result = await session.execute(
        select(CustomerConsent).where(CustomerConsent.customer_id == customer_id)
    )
    return list(result.scalars().all())


async def consent_add(session: AsyncSession, row: CustomerConsent) -> CustomerConsent:
    session.add(row)
    await session.flush()
    return row


async def b2b_links_by_customer(session: AsyncSession, customer_id: UUID) -> list[CustomerB2BLink]:
    result = await session.execute(
        select(CustomerB2BLink)
        .where(CustomerB2BLink.customer_id == customer_id)
        .order_by(CustomerB2BLink.created_at.asc())
    )
    return list(result.scalars().all())


async def b2b_link_by_customer_counterparty(
    session: AsyncSession, customer_id: UUID, counterparty_id: UUID
) -> CustomerB2BLink | None:
    result = await session.execute(
        select(CustomerB2BLink).where(
            CustomerB2BLink.customer_id == customer_id,
            CustomerB2BLink.counterparty_id == counterparty_id,
        )
    )
    return result.scalar_one_or_none()


async def b2b_link_get_for_customer(
    session: AsyncSession, customer_id: UUID, link_id: UUID
) -> CustomerB2BLink | None:
    result = await session.execute(
        select(CustomerB2BLink).where(
            CustomerB2BLink.id == link_id,
            CustomerB2BLink.customer_id == customer_id,
        )
    )
    return result.scalar_one_or_none()


async def b2b_link_add(session: AsyncSession, row: CustomerB2BLink) -> CustomerB2BLink:
    session.add(row)
    await session.flush()
    return row


async def b2b_link_delete(session: AsyncSession, row: CustomerB2BLink) -> None:
    await session.execute(delete(CustomerB2BLink).where(CustomerB2BLink.id == row.id))
    await session.flush()
