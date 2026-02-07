"""add price and status to listings 

Revision ID: 633144c54ee9
Revises: 136943391b9d
Create Date: 2026-02-07 20:20:20.843983

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '633144c54ee9'
down_revision: Union[str, Sequence[str], None] = '136943391b9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("listings", sa.Column("price", sa.Integer(), nullable=True))
    op.add_column(
        "listings",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="ON_SALE"
        )
    )

def downgrade():
    op.drop_column("listings", "status")
    op.drop_column("listings", "price")
