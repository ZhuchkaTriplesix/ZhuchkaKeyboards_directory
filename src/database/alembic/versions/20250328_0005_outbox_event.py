"""Transactional outbox for directory integration events.

Revision ID: 20250328_0005
Revises: 20250327_0004
Create Date: 2025-03-28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20250328_0005"
down_revision = "20250327_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox_event",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("payload", JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_outbox_event_event_type", "outbox_event", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_outbox_event_event_type", table_name="outbox_event")
    op.drop_table("outbox_event")
