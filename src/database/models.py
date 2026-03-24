"""Domain ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from src.database.base import Base


class Customer(Base):
    """Customer profile keyed by Auth JWT ``sub`` (UUID)."""

    __repr_attrs__ = ("subject", "email")

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), unique=True, index=True, nullable=False
    )
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default="b2c")
    locale: Mapped[str | None] = mapped_column(String(32), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    addresses: Mapped[list[CustomerAddress]] = relationship(
        "CustomerAddress",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    consents: Mapped[list[CustomerConsent]] = relationship(
        "CustomerConsent",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    b2b_links: Mapped[list[CustomerB2BLink]] = relationship(
        "CustomerB2BLink",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CustomerAddress(Base):
    """Saved postal address for a customer (billing / shipping)."""

    __repr_attrs__ = ("kind", "line1")

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("customer.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    line1: Mapped[str] = mapped_column(String(255), nullable=False)
    line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    region: Mapped[str | None] = mapped_column(String(128), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    customer: Mapped[Customer] = relationship("Customer", back_populates="addresses")


class CustomerConsent(Base):
    """Legal / marketing consent per customer (one row per consent_type)."""

    __table_args__ = (
        UniqueConstraint("customer_id", "consent_type", name="uq_customer_consent_customer_type"),
    )
    __repr_attrs__ = ("consent_type", "document_version")

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("customer.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    consent_type: Mapped[str] = mapped_column(String(32), nullable=False)
    document_version: Mapped[str] = mapped_column(String(64), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    customer: Mapped[Customer] = relationship("Customer", back_populates="consents")


class CustomerB2BLink(Base):
    """Link between a customer profile and a counterparty (UUID from counterparties service)."""

    __table_args__ = (
        UniqueConstraint(
            "customer_id",
            "counterparty_id",
            name="uq_customer_b2b_customer_counterparty",
        ),
    )
    __repr_attrs__ = ("counterparty_id", "contact_role")

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("customer.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    counterparty_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    contact_role: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    customer: Mapped[Customer] = relationship("Customer", back_populates="b2b_links")
