"""add price and status to stores

Revision ID: 136943391b9d
Revises: dba9fa10ede8
Create Date: 2026-02-07 20:13:57.953937

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '136943391b9d'
down_revision: Union[str, Sequence[str], None] = 'dba9fa10ede8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # stores 정리
    op.drop_column("stores", "price")
    op.drop_column("stores", "status")

    # releases 정리
    op.drop_column("releases", "color")
    op.drop_column("releases", "format")


def downgrade() -> None:
    op.add_column("stores", sa.Column("price", sa.Integer(), nullable=True))
    op.add_column(
        "stores",
        sa.Column("status", sa.String(length=20), nullable=False)
    )

    op.add_column("releases", sa.Column("color", sa.String(), nullable=True))
    op.add_column("releases", sa.Column("format", sa.String(), nullable=True))
