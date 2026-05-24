"""add_cover_url_to_songs

Revision ID: f1e2d3c4b5a6
Revises: d1e2f3a4b5c6
Create Date: 2026-05-24 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f1e2d3c4b5a6"
down_revision: str | Sequence[str] | None = "d1e2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "songs",
        sa.Column("cover_url", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("songs", "cover_url")
