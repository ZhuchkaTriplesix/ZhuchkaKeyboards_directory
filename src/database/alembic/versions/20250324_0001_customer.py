"""Customer profile table (Auth ``sub``).

Revision ID: 20250324_0001
Revises:
Create Date: 2025-03-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "20250324_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("subject", UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("kind", sa.String(16), nullable=False, server_default="b2c"),
        sa.Column("locale", sa.String(32), nullable=True),
        sa.Column("timezone", sa.String(64), nullable=True),
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
        sa.UniqueConstraint("subject", name="uq_customer_subject"),
    )


def downgrade() -> None:
    op.drop_table("customer")
