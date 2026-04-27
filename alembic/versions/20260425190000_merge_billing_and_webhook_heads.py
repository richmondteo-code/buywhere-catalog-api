"""merge billing and webhook heads before affiliate click tracking

Revision ID: 20260425190000
Revises: 20260425153000, 20260425173000
Create Date: 2026-04-25 19:00:00.000000
"""

from typing import Sequence, Union


revision: str = "20260425190000"
down_revision: Union[str, Sequence[str], None] = (
    "20260425153000",
    "20260425173000",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
