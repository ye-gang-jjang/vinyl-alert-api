"""add price to pending candidates

Revision ID: 4b8ce1d2aa31
Revises: 9d5b6f2a1c11
Create Date: 2026-04-09 20:25:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4b8ce1d2aa31"
down_revision: Union[str, None] = "9d5b6f2a1c11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("pending_candidates", sa.Column("price", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("pending_candidates", "price")
