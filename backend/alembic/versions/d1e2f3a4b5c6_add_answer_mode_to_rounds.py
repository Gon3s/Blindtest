"""add_answer_mode_to_rounds

Revision ID: d1e2f3a4b5c6
Revises: c1d2e3f4a5b6
Create Date: 2026-05-22 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d1e2f3a4b5c6"
down_revision: str | Sequence[str] | None = "c1d2e3f4a5b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "rounds",
        sa.Column(
            "answer_mode",
            sa.String(32),
            nullable=False,
            server_default="both",
        ),
    )


def downgrade() -> None:
    op.drop_column("rounds", "answer_mode")
