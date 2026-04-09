"""drop status from listings

Revision ID: 9d5b6f2a1c11
Revises: f1743b5b9d01
Create Date: 2026-04-09 18:55:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9d5b6f2a1c11"
down_revision: Union[str, None] = "f1743b5b9d01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("listings", "status")


def downgrade() -> None:
    op.add_column(
        "listings",
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ON_SALE"),
    )
