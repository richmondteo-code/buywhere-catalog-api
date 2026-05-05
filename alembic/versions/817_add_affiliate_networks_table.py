"""Add affiliate_networks table for HMAC key management.

BUY-12197 — Phase 2: HMAC key management for affiliate webhook secrets.

Revision ID: 817
Revises: 816
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "817"
down_revision = "816"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "affiliate_networks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=True),
        sa.Column("webhook_secret_encrypted", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_affiliate_networks_name"),
    )
    op.create_index("idx_aff_network_name", "affiliate_networks", ["name"])


def downgrade() -> None:
    op.drop_index("idx_aff_network_name", table_name="affiliate_networks")
    op.drop_table("affiliate_networks")
