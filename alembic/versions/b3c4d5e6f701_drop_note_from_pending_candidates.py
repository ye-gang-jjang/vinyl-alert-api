"""drop note from pending candidates

Revision ID: b3c4d5e6f701
Revises: 8b0f9f4b2d7e
Create Date: 2026-04-24 17:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3c4d5e6f701"
down_revision: Union[str, None] = "8b0f9f4b2d7e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("pending_candidates", "note")


def downgrade() -> None:
    op.add_column("pending_candidates", sa.Column("note", sa.Text(), nullable=True))
