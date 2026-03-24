"""Public API schemas for `/api/v1`."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerKind(StrEnum):
    b2c = "b2c"
    b2b = "b2b"


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject: UUID
    email: str | None = None
    display_name: str | None = None
    phone: str | None = None
    kind: CustomerKind
    locale: str | None = None
    timezone: str | None = None
    created_at: datetime
    updated_at: datetime


class CustomerPatch(BaseModel):
    email: EmailStr | None = None
    display_name: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=64)
    kind: CustomerKind | None = None
    locale: str | None = Field(None, max_length=32)
    timezone: str | None = Field(None, max_length=64)
