"""Add affiliate_import_jobs and affiliate_commissions tables for Phase 3 batch CSV import.

BUY-12198: Batch CSV import for affiliate commissions, report/forecast endpoints,
and currency conversion support.

Revision ID: 815
Revises: 814
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "815"
down_revision = "814"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "affiliate_import_jobs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("network", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_succeeded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_import_jobs_network", "affiliate_import_jobs", ["network"])
    op.create_index("idx_import_jobs_status", "affiliate_import_jobs", ["status"])
    op.create_index("idx_import_jobs_created_at", "affiliate_import_jobs", ["created_at"])

    op.create_table(
        "affiliate_commissions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("click_id", sa.Text(), nullable=False),
        sa.Column("conversion_id", sa.Text(), nullable=True),
        sa.Column("product_id", sa.BigInteger(), nullable=True),
        sa.Column("network", sa.Text(), nullable=False),
        sa.Column("commission_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("commission_currency", sa.String(3), nullable=False),
        sa.Column("commission_amount_sgd", sa.Numeric(12, 2), nullable=True),
        sa.Column("order_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("order_currency", sa.String(3), nullable=True),
        sa.Column("order_value_sgd", sa.Numeric(12, 2), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("import_job_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("click_id", name="uq_affiliate_commissions_click_id"),
    )
    op.create_index("idx_ac_network", "affiliate_commissions", ["network"])
    op.create_index("idx_ac_status", "affiliate_commissions", ["status"])
    op.create_index("idx_ac_timestamp", "affiliate_commissions", ["timestamp"])
    op.create_index("idx_ac_import_job_id", "affiliate_commissions", ["import_job_id"])
    op.create_index("idx_ac_network_timestamp", "affiliate_commissions", ["network", "timestamp"])
    op.create_index(
        "idx_ac_network_status_timestamp",
        "affiliate_commissions",
        ["network", "status", "timestamp"],
    )


def downgrade() -> None:
    op.drop_index("idx_ac_network_status_timestamp", table_name="affiliate_commissions")
    op.drop_index("idx_ac_network_timestamp", table_name="affiliate_commissions")
    op.drop_index("idx_ac_import_job_id", table_name="affiliate_commissions")
    op.drop_index("idx_ac_timestamp", table_name="affiliate_commissions")
    op.drop_index("idx_ac_status", table_name="affiliate_commissions")
    op.drop_index("idx_ac_network", table_name="affiliate_commissions")
    op.drop_table("affiliate_commissions")
    op.drop_index("idx_import_jobs_created_at", table_name="affiliate_import_jobs")
    op.drop_index("idx_import_jobs_status", table_name="affiliate_import_jobs")
    op.drop_index("idx_import_jobs_network", table_name="affiliate_import_jobs")
    op.drop_table("affiliate_import_jobs")
