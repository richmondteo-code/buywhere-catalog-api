"""Add agent_framework column to query_log

Revision ID: 811
Revises: 810
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa


revision = "811"
down_revision = "810"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("query_log", sa.Column("agent_framework", sa.Text(), nullable=True))
    op.create_index("idx_query_log_agent_framework", "query_log", ["agent_framework"])


def downgrade() -> None:
    op.drop_index("idx_query_log_agent_framework", table_name="query_log")
    op.drop_column("query_log", "agent_framework")
