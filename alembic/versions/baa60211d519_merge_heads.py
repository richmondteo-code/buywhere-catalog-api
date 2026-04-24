"""merge_heads

Revision ID: baa60211d519
Revises: 034, 034_add_seo_keyword_tracker, 034c
Create Date: 2026-04-24 08:21:56.543176

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'baa60211d519'
down_revision: Union[str, None] = ('034', '034_add_seo_keyword_tracker', '034c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
