"""Wire-level event type strings and JSON payloads for the outbox."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

# Event types (docs/microservices/02-directory.md)
DIRECTORY_CUSTOMER_CREATED = "directory.customer.created"
DIRECTORY_CUSTOMER_UPDATED = "directory.customer.updated"
DIRECTORY_CONSENT_CHANGED = "directory.consent.changed"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class CustomerCreatedPayload(BaseModel):
    customer_id: UUID
    subject: UUID
    occurred_at: datetime = Field(default_factory=_utcnow)


class CustomerUpdatedPayload(BaseModel):
    customer_id: UUID
    subject: UUID
    occurred_at: datetime = Field(default_factory=_utcnow)


class ConsentChangedPayload(BaseModel):
    customer_id: UUID
    consent_type: str
    document_version: str | None = None
    granted: bool
    occurred_at: datetime = Field(default_factory=_utcnow)


def payload_to_json(obj: BaseModel) -> dict[str, Any]:
    """JSON-serializable dict for DB JSONB (UUID → str)."""
    return obj.model_dump(mode="json")
