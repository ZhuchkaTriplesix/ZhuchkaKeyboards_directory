"""Public API schemas for `/api/v1`."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


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


class AddressKind(StrEnum):
    billing = "billing"
    shipping = "shipping"


class AddressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    kind: AddressKind
    line1: str
    line2: str | None = None
    city: str | None = None
    region: str | None = None
    postal_code: str | None = None
    country: str = Field(..., min_length=2, max_length=2)
    is_default: bool
    created_at: datetime
    updated_at: datetime


class AddressCreate(BaseModel):
    kind: AddressKind
    line1: str = Field(..., min_length=1, max_length=255)
    line2: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=128)
    region: str | None = Field(None, max_length=128)
    postal_code: str | None = Field(None, max_length=32)
    country: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2")
    is_default: bool = False

    @field_validator("country")
    @classmethod
    def country_upper(cls, v: str) -> str:
        return v.strip().upper()


class AddressPatch(BaseModel):
    kind: AddressKind | None = None
    line1: str | None = Field(None, min_length=1, max_length=255)
    line2: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=128)
    region: str | None = Field(None, max_length=128)
    postal_code: str | None = Field(None, max_length=32)
    country: str | None = Field(None, min_length=2, max_length=2)
    is_default: bool | None = None

    @field_validator("country")
    @classmethod
    def country_upper(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.strip().upper()
