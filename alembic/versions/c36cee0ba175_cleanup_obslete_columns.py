"""cleanup obslete columns

Revision ID: c36cee0ba175
Revises: 633144c54ee9
Create Date: 2026-02-07 20:26:50.530185

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c36cee0ba175'
down_revision: Union[str, Sequence[str], None] = '633144c54ee9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
