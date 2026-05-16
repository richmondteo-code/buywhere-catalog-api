"""Add Stripe integration columns to api_keys

Adds stripe_customer_id, stripe_subscription_id, daily_request_count,
daily_reset_at, and revoked_at to support Stripe-driven key provisioning
and daily rate limit resets (BUY-18467 / BUY-18470).

Revision ID: 810
Revises: 809
Create Date: 2026-05-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "810"
down_revision = "809"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "api_keys",
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "api_keys",
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "api_keys",
        sa.Column(
            "daily_request_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "api_keys",
        sa.Column(
            "daily_reset_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW() + INTERVAL '1 day'"),
        ),
    )
    op.add_column(
        "api_keys",
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # Partial index for fast key lookups on active keys
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_api_keys_hash
        ON api_keys(key_hash)
        WHERE is_active = true
        """
    )

    # Update default tier from 'basic' to 'free' for new rows
    op.execute(
        "ALTER TABLE api_keys ALTER COLUMN tier SET DEFAULT 'free'"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_api_keys_hash")
    op.drop_column("api_keys", "revoked_at")
    op.drop_column("api_keys", "daily_reset_at")
    op.drop_column("api_keys", "daily_request_count")
    op.drop_column("api_keys", "stripe_subscription_id")
    op.drop_column("api_keys", "stripe_customer_id")
    op.execute("ALTER TABLE api_keys ALTER COLUMN tier SET DEFAULT 'basic'")
