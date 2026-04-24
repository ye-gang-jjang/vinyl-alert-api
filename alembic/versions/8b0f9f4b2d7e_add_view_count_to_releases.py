"""add view count to releases

Revision ID: 8b0f9f4b2d7e
Revises: 6f3c2b7a901d
Create Date: 2026-04-24 15:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8b0f9f4b2d7e"
down_revision: Union[str, None] = "6f3c2b7a901d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "releases",
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("releases", "view_count")
