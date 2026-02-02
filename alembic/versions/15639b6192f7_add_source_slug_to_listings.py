"""add source_slug to listings

Revision ID: 15639b6192f7
Revises: 02965abb2c91
Create Date: 2026-02-02 17:34:59.975295

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15639b6192f7'
down_revision: Union[str, Sequence[str], None] = '02965abb2c91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "listings",
        sa.Column("source_slug", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_listings_source_slug",
        "listings",
        ["source_slug"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_listings_source_slug", table_name="listings")
    op.drop_column("listings", "source_slug")
