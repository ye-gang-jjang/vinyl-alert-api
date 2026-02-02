"""drop listing legacy columns

Revision ID: dba9fa10ede8
Revises: 883092e87150
Create Date: 2026-02-02 21:31:56.186568

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dba9fa10ede8'
down_revision: Union[str, Sequence[str], None] = '883092e87150'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) source_slug를 NOT NULL로 강제 (NULL이 없어야 함)
    op.alter_column(
        "listings",
        "source_slug",
        existing_type=sa.String(),
        nullable=False,
    )

    # 2) stores.slug와 FK 연결 (stores.slug가 unique여야 함)
    op.create_foreign_key(
        "fk_listings_source_slug_stores_slug",
        "listings",
        "stores",
        ["source_slug"],
        ["slug"],
        ondelete="RESTRICT",
    )

    # 3) legacy 컬럼 제거
    op.drop_column("listings", "source_name")
    op.drop_column("listings", "image_url")


def downgrade() -> None:
    # 되돌리기
    op.add_column("listings", sa.Column("image_url", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("source_name", sa.String(), nullable=True))

    op.drop_constraint(
        "fk_listings_source_slug_stores_slug",
        "listings",
        type_="foreignkey",
    )

    op.alter_column(
        "listings",
        "source_slug",
        existing_type=sa.String(),
        nullable=True,
    )