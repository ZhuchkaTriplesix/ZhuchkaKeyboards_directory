"""Customer consent records (privacy / marketing).

Revision ID: 20250326_0003
Revises: 20250325_0002
Create Date: 2025-03-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "20250326_0003"
down_revision = "20250325_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_consent",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("customer_id", UUID(as_uuid=True), nullable=False),
        sa.Column("consent_type", sa.String(32), nullable=False),
        sa.Column("document_version", sa.String(64), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customer.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "customer_id",
            "consent_type",
            name="uq_customer_consent_customer_type",
        ),
    )
    op.create_index(
        "ix_customer_consent_customer_id",
        "customer_consent",
        ["customer_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_customer_consent_customer_id", table_name="customer_consent")
    op.drop_table("customer_consent")
