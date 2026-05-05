"""Add commission_daily table for pre-aggregated daily revenue rollups.

BUY-12212 — Build commission tracking database and daily revenue dashboard.

Revision ID: 818
Revises: 817
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa


revision = "818"
down_revision = "817"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commission_daily",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("network", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'approved'")),
        sa.Column("commission_count", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("commission_amount_sgd", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("order_value_sgd", sa.Numeric(14, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date", "network", "status", name="uq_commission_daily_date_network_status"),
    )
    op.create_index("idx_commission_daily_date", "commission_daily", ["date"])
    op.create_index("idx_commission_daily_network", "commission_daily", ["network"])
    op.create_index("idx_commission_daily_date_network", "commission_daily", ["date", "network"])


def downgrade() -> None:
    op.drop_index("idx_commission_daily_date_network", table_name="commission_daily")
    op.drop_index("idx_commission_daily_network", table_name="commission_daily")
    op.drop_index("idx_commission_daily_date", table_name="commission_daily")
    op.drop_table("commission_daily")
