"""Business logic for `/api/v1` customer self-service."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.v1.dal import customer_by_subject, customer_create
from src.routers.v1.schemas import CustomerOut, CustomerPatch


async def get_or_create_me(session: AsyncSession, subject: UUID) -> CustomerOut:
    row = await customer_by_subject(session, subject)
    if row is None:
        row = await customer_create(session, subject)
        await session.flush()
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
