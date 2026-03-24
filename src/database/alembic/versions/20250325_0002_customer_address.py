"""Customer address rows (billing / shipping).

Revision ID: 20250325_0002
Revises: 20250324_0001
Create Date: 2025-03-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "20250325_0002"
down_revision = "20250324_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_address",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("customer_id", UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("line1", sa.String(255), nullable=False),
        sa.Column("line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("region", sa.String(128), nullable=True),
        sa.Column("postal_code", sa.String(32), nullable=True),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
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
    )
    op.create_index(
        "ix_customer_address_customer_id",
        "customer_address",
        ["customer_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_customer_address_customer_id", table_name="customer_address")
    op.drop_table("customer_address")
