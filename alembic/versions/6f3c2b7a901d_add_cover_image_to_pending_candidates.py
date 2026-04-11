"""add cover image to pending candidates

Revision ID: 6f3c2b7a901d
Revises: 4b8ce1d2aa31
Create Date: 2026-04-11 18:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6f3c2b7a901d"
down_revision: Union[str, None] = "4b8ce1d2aa31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("pending_candidates", sa.Column("cover_image_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("pending_candidates", "cover_image_url")
