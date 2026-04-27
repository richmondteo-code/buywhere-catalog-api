"""Add affiliate click tracking tables for session-based revenue attribution

Revision ID: 20260425200000
Revises: 20260425190000
Create Date: 2026-04-25 20:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "20260425200000"
down_revision = "20260425190000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "affiliate_clicks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("merchant", sa.String(), nullable=False),
        sa.Column("platform", sa.String(), nullable=True),
        sa.Column("tracking_id", sa.String(), nullable=True),
        sa.Column("api_key_id", sa.String(), nullable=True),
        sa.Column("agent_id", sa.String(), nullable=True),
        sa.Column("affiliate_partner", sa.String(), nullable=True),
        sa.Column("destination_url", sa.Text(), nullable=False),
        sa.Column("referrer", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("user_ip", sa.Text(), nullable=True),
        sa.Column("country", sa.String(2), nullable=True),
        sa.Column(
            "clicked_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_affiliate_clicks_session_product", "affiliate_clicks", ["session_id", "product_id"])
    op.create_index("idx_affiliate_clicks_merchant", "affiliate_clicks", ["merchant"])
    op.create_index("idx_affiliate_clicks_clicked_at", "affiliate_clicks", ["clicked_at"])
    op.create_index("idx_affiliate_clicks_api_key_id", "affiliate_clicks", ["api_key_id"])
    op.create_index("idx_affiliate_clicks_tracking_id", "affiliate_clicks", ["tracking_id"])
    op.create_index("idx_affiliate_clicks_session_id", "affiliate_clicks", ["session_id"])
    op.create_index("idx_affiliate_clicks_product_id", "affiliate_clicks", ["product_id"])

    op.create_table(
        "affiliate_conversions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("click_id", sa.BigInteger(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("merchant", sa.String(), nullable=False),
        sa.Column("platform", sa.String(), nullable=True),
        sa.Column("tracking_id", sa.String(), nullable=True),
        sa.Column("api_key_id", sa.String(), nullable=True),
        sa.Column("agent_id", sa.String(), nullable=True),
        sa.Column("affiliate_partner", sa.String(), nullable=True),
        sa.Column("conversion_revenue", sa.Numeric(12, 4), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="SGD"),
        sa.Column("conversion_type", sa.String(32), nullable=True),
        sa.Column("conversion_data", JSONB(), nullable=True),
        sa.Column(
            "converted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_affiliate_conversions_click_id", "affiliate_conversions", ["click_id"])
    op.create_index("idx_affiliate_conversions_session_id", "affiliate_conversions", ["session_id"])
    op.create_index("idx_affiliate_conversions_product_id", "affiliate_conversions", ["product_id"])
    op.create_index("idx_affiliate_conversions_merchant", "affiliate_conversions", ["merchant"])
    op.create_index("idx_affiliate_conversions_conversion_type", "affiliate_conversions", ["conversion_type"])
    op.create_index("idx_affiliate_conversions_converted_at", "affiliate_conversions", ["converted_at"])
    op.create_index("idx_affiliate_conversions_api_key_id", "affiliate_conversions", ["api_key_id"])


def downgrade() -> None:
    op.drop_table("affiliate_conversions")
    op.drop_table("affiliate_clicks")
