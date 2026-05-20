"""uq_answers_song_participant

Revision ID: c1d2e3f4a5b6
Revises: b9c1d2e3f4a5
Create Date: 2026-05-20 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "b9c1d2e3f4a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Keep only the latest answer per (song_id, participant_id)
    op.execute(
        """
        DELETE FROM answers a
        USING (
            SELECT song_id, participant_id, MAX(submitted_at) AS keep_at
            FROM answers
            GROUP BY song_id, participant_id
        ) keep
        WHERE a.song_id = keep.song_id
          AND a.participant_id = keep.participant_id
          AND a.submitted_at < keep.keep_at
        """
    )
    op.create_unique_constraint(
        "uq_answers_song_participant", "answers", ["song_id", "participant_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_answers_song_participant", "answers", type_="unique")
