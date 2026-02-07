"""cleanup obsolete columns

Revision ID: 0ed1a1fca229
Revises: c36cee0ba175
Create Date: 2026-02-07 20:30:10.062467

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ed1a1fca229'
down_revision: Union[str, Sequence[str], None] = 'c36cee0ba175'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
