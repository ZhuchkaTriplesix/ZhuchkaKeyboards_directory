"""Transactional outbox writes (same DB session as domain changes)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import OutboxEvent


async def enqueue_outbox(session: AsyncSession, event_type: str, payload: dict[str, Any]) -> None:
    session.add(OutboxEvent(event_type=event_type, payload=payload))
