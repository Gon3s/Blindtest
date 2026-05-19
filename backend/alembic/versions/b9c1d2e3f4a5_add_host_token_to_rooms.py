"""add_host_token_to_rooms

Revision ID: b9c1d2e3f4a5
Revises: a4f7d3e8b2c5
Create Date: 2026-05-19 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "b9c1d2e3f4a5"
down_revision: Union[str, Sequence[str], None] = "a4f7d3e8b2c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "rooms",
        sa.Column(
            "host_token",
            sa.String(64),
            nullable=False,
            server_default=sa.text(
                "replace(gen_random_uuid()::text, '-', '')"
                " || replace(gen_random_uuid()::text, '-', '')"
            ),
        ),
    )
    # Remove server_default after backfill so new rows must provide the value explicitly
    op.alter_column("rooms", "host_token", server_default=None)


def downgrade() -> None:
    op.drop_column("rooms", "host_token")
