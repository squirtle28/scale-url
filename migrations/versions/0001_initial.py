"""create urls table

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "urls",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("short_code", sa.String(length=20), nullable=False),
        sa.Column("long_url", sa.Text(), nullable=False),
        sa.Column(
            "custom_alias", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "click_count", sa.BigInteger(), nullable=False, server_default="0"
        ),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
    )
    # A single unique index both enforces uniqueness and speeds up the
    # short_code lookups that happen on every redirect request.
    op.create_index("ix_urls_short_code", "urls", ["short_code"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_urls_short_code", table_name="urls")
    op.drop_table("urls")
