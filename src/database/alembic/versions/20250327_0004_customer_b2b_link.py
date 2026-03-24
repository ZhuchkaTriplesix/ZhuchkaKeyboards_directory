"""B2B link: customer ↔ counterparty id (external service).

Revision ID: 20250327_0004
Revises: 20250326_0003
Create Date: 2025-03-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "20250327_0004"
down_revision = "20250326_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_b2b_link",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("customer_id", UUID(as_uuid=True), nullable=False),
        sa.Column("counterparty_id", UUID(as_uuid=True), nullable=False),
        sa.Column("contact_role", sa.String(64), nullable=False),
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
            "counterparty_id",
            name="uq_customer_b2b_customer_counterparty",
        ),
    )
    op.create_index(
        "ix_customer_b2b_link_customer_id",
        "customer_b2b_link",
        ["customer_id"],
    )
    op.create_index(
        "ix_customer_b2b_link_counterparty_id",
        "customer_b2b_link",
        ["counterparty_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_customer_b2b_link_counterparty_id", table_name="customer_b2b_link")
    op.drop_index("ix_customer_b2b_link_customer_id", table_name="customer_b2b_link")
    op.drop_table("customer_b2b_link")
