"""create pending candidates table

Revision ID: f1743b5b9d01
Revises: 0ed1a1fca229
Create Date: 2026-04-09 18:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f1743b5b9d01"
down_revision: Union[str, None] = "283696c33eca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pending_candidates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("artist_name", sa.String(), nullable=False),
        sa.Column("normalized_artist_name", sa.String(), nullable=False),
        sa.Column("album_title", sa.String(), nullable=False),
        sa.Column("normalized_album_title", sa.String(), nullable=False),
        sa.Column("source_slug", sa.String(), nullable=False),
        sa.Column("source_product_title", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("matched_release_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["matched_release_id"], ["releases.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pending_candidates_id"), "pending_candidates", ["id"], unique=False)
    op.create_index(op.f("ix_pending_candidates_artist_name"), "pending_candidates", ["artist_name"], unique=False)
    op.create_index(op.f("ix_pending_candidates_normalized_artist_name"), "pending_candidates", ["normalized_artist_name"], unique=False)
    op.create_index(op.f("ix_pending_candidates_normalized_album_title"), "pending_candidates", ["normalized_album_title"], unique=False)
    op.create_index(op.f("ix_pending_candidates_source_slug"), "pending_candidates", ["source_slug"], unique=False)
    op.create_index(op.f("ix_pending_candidates_status"), "pending_candidates", ["status"], unique=False)
    op.create_index(op.f("ix_pending_candidates_url"), "pending_candidates", ["url"], unique=True)
    op.create_index(op.f("ix_pending_candidates_matched_release_id"), "pending_candidates", ["matched_release_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_pending_candidates_matched_release_id"), table_name="pending_candidates")
    op.drop_index(op.f("ix_pending_candidates_url"), table_name="pending_candidates")
    op.drop_index(op.f("ix_pending_candidates_status"), table_name="pending_candidates")
    op.drop_index(op.f("ix_pending_candidates_source_slug"), table_name="pending_candidates")
    op.drop_index(op.f("ix_pending_candidates_normalized_album_title"), table_name="pending_candidates")
    op.drop_index(op.f("ix_pending_candidates_normalized_artist_name"), table_name="pending_candidates")
    op.drop_index(op.f("ix_pending_candidates_artist_name"), table_name="pending_candidates")
    op.drop_index(op.f("ix_pending_candidates_id"), table_name="pending_candidates")
    op.drop_table("pending_candidates")
