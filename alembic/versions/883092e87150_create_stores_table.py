"""create stores table

Revision ID: 883092e87150
Revises: 15639b6192f7
Create Date: 2026-02-02 17:58:30.452509

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '883092e87150'
down_revision: Union[str, Sequence[str], None] = '15639b6192f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("icon_url", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_stores_id", "stores", ["id"])
    op.create_index("ix_stores_name", "stores", ["name"], unique=True)
    op.create_index("ix_stores_slug", "stores", ["slug"], unique=True)

def downgrade() -> None:
    op.drop_index("ix_stores_slug", table_name="stores")
    op.drop_index("ix_stores_name", table_name="stores")
    op.drop_index("ix_stores_id", table_name="stores")
    op.drop_table("stores")