"""Add merchant_queue table for validated Shopify merchant ingestion pipeline.

Revision ID: 812
Revises: 811
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "812"
down_revision = "811"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "merchant_queue",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("domain", sa.Text(), nullable=False),
        sa.Column("platform", sa.Text(), nullable=False, server_default="shopify"),
        sa.Column("vertical", sa.Text(), nullable=True),
        sa.Column("country", sa.String(2), nullable=False, server_default="US"),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("assigned_agent", sa.Text(), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain", "platform", name="merchant_queue_domain_platform_unique"),
    )
    op.create_index("idx_merchant_queue_status", "merchant_queue", ["status"])
    op.create_index("idx_merchant_queue_platform", "merchant_queue", ["platform"])
    op.create_index("idx_merchant_queue_country", "merchant_queue", ["country"])
    op.create_index("idx_merchant_queue_assigned_agent", "merchant_queue", ["assigned_agent"])
    op.create_index("idx_merchant_queue_status_created", "merchant_queue", ["status", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_merchant_queue_status_created", table_name="merchant_queue")
    op.drop_index("idx_merchant_queue_assigned_agent", table_name="merchant_queue")
    op.drop_index("idx_merchant_queue_country", table_name="merchant_queue")
    op.drop_index("idx_merchant_queue_platform", table_name="merchant_queue")
    op.drop_index("idx_merchant_queue_status", table_name="merchant_queue")
    op.drop_table("merchant_queue")
