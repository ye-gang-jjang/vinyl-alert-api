"""add default to listings.collected_at

Revision ID: 283696c33eca
Revises: 0ed1a1fca229
Create Date: 2026-02-07 21:52:11.561811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '283696c33eca'
down_revision: Union[str, Sequence[str], None] = '0ed1a1fca229'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 혹시라도 기존 null 있으면 채움
    op.execute("""
        UPDATE listings
        SET collected_at = NOW()
        WHERE collected_at IS NULL
    """)

    # DB 레벨 default 추가
    op.alter_column(
        "listings",
        "collected_at",
        server_default=sa.text("NOW()"),
        existing_nullable=False,
    )

def downgrade():
    op.alter_column(
        "listings",
        "collected_at",
        server_default=None,
        existing_nullable=False,
    )