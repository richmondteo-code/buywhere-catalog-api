"""Add analytics columns to query_log for MCP testing metrics

Adds: mcp_tool_name, ai_model, region, result_count for MCP testing metrics
and endpoint-level aggregation.

Revision ID: 810
Revises: 809_add_merchant_registry_columns
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


revision = "810"
down_revision = "809_add_merchant_registry_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("query_log", sa.Column("mcp_tool_name", sa.Text(), nullable=True))
    op.add_column("query_log", sa.Column("ai_model", sa.Text(), nullable=True))
    op.add_column("query_log", sa.Column("region", sa.String(length=10), nullable=True))
    op.add_column("query_log", sa.Column("result_count", sa.Integer(), nullable=True))
    op.add_column("query_log", sa.Column("keywords", ARRAY(sa.Text()), nullable=True))
    op.add_column("query_log", sa.Column("categories", ARRAY(sa.Text()), nullable=True))
    op.create_index("idx_query_log_mcp_tool", "query_log", ["mcp_tool_name"])
    op.create_index("idx_query_log_ai_model", "query_log", ["ai_model"])
    op.create_index("idx_query_log_region", "query_log", ["region"])


def downgrade() -> None:
    op.drop_index("idx_query_log_region", table_name="query_log")
    op.drop_index("idx_query_log_ai_model", table_name="query_log")
    op.drop_index("idx_query_log_mcp_tool", table_name="query_log")
    op.drop_column("query_log", "categories")
    op.drop_column("query_log", "keywords")
    op.drop_column("query_log", "result_count")
    op.drop_column("query_log", "region")
    op.drop_column("query_log", "ai_model")
    op.drop_column("query_log", "mcp_tool_name")
