"""initial_empty

Revision ID: cc53e5086ad8
Revises:
Create Date: 2026-05-14 11:36:41.792183

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "cc53e5086ad8"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
