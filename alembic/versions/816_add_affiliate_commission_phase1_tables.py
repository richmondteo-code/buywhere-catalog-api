"""Add Phase 1 affiliate commission tables and extend affiliate_commissions.

BUY-12196 — Phase 1 foundation for affiliate commission infrastructure.
Adds affiliate_product_mappings, affiliate_rate_tables, and missing columns
to the existing affiliate_commissions table (created by 815).

Revision ID: 816
Revises: 815
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "816"
down_revision = "815"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Extend affiliate_commissions with Phase 1 columns ──────────────
    op.add_column("affiliate_commissions", sa.Column("network_product_id", sa.Text(), nullable=True))
    op.add_column("affiliate_commissions", sa.Column("buywhere_product_id", sa.BigInteger(), nullable=True))
    op.add_column("affiliate_commissions", sa.Column("status_history", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("affiliate_commissions", sa.Column("earned_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("affiliate_commissions", sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True))
    op.add_column("affiliate_commissions", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True))
    op.add_column("affiliate_commissions", sa.Column("metadata", postgresql.JSONB(), nullable=True))

    # migrate existing data: copy timestamp → earned_at, copy product_id → buywhere_product_id
    op.execute("UPDATE affiliate_commissions SET earned_at = timestamp WHERE earned_at IS NULL")
    op.execute("UPDATE affiliate_commissions SET received_at = created_at WHERE received_at IS NULL")
    op.execute("UPDATE affiliate_commissions SET updated_at = created_at WHERE updated_at IS NULL")
    op.execute("UPDATE affiliate_commissions SET buywhere_product_id = product_id WHERE buywhere_product_id IS NULL")

    # make new columns NOT NULL after backfill
    op.alter_column("affiliate_commissions", "network_product_id", nullable=False)
    op.alter_column("affiliate_commissions", "earned_at", nullable=False)
    op.alter_column("affiliate_commissions", "received_at", nullable=False)
    op.alter_column("affiliate_commissions", "updated_at", nullable=False)

    op.create_foreign_key(
        "fk_aff_comm_buywhere_product",
        "affiliate_commissions", "products",
        ["buywhere_product_id"], ["id"],
    )
    op.create_index("idx_aff_comm_network_product_id", "affiliate_commissions", ["network_product_id"])
    op.create_index("idx_aff_comm_buywhere_product_id", "affiliate_commissions", ["buywhere_product_id"])
    op.create_index("idx_aff_comm_earned_at", "affiliate_commissions", ["earned_at"])
    op.create_index("idx_aff_comm_updated_at", "affiliate_commissions", ["updated_at"])

    # ── affiliate_product_mappings ─────────────────────────────────────
    op.create_table(
        "affiliate_product_mappings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("network", sa.Text(), nullable=False),
        sa.Column("network_product_id", sa.Text(), nullable=False),
        sa.Column("buywhere_product_id", sa.BigInteger(), nullable=False),
        sa.Column("confidence", sa.Text(), nullable=False, server_default="exact"),
        sa.Column("mapped_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("network", "network_product_id", name="affiliate_product_mappings_network_sku_unique"),
        sa.ForeignKeyConstraint(["buywhere_product_id"], ["products.id"], name="fk_affiliate_product_mappings_product"),
    )
    op.create_index("idx_aff_map_network", "affiliate_product_mappings", ["network"])
    op.create_index("idx_aff_map_product_id", "affiliate_product_mappings", ["buywhere_product_id"])

    # ── affiliate_rate_tables ──────────────────────────────────────────
    op.create_table(
        "affiliate_rate_tables",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("network", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False, server_default="default"),
        sa.Column("rate", sa.Numeric(5, 4), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_aff_rate_network", "affiliate_rate_tables", ["network"])
    op.create_index("idx_aff_rate_network_category", "affiliate_rate_tables", ["network", "category"])


def downgrade() -> None:
    # ── affiliate_rate_tables ──────────────────────────────────────────
    op.drop_index("idx_aff_rate_network_category", table_name="affiliate_rate_tables")
    op.drop_index("idx_aff_rate_network", table_name="affiliate_rate_tables")
    op.drop_table("affiliate_rate_tables")

    # ── affiliate_product_mappings ─────────────────────────────────────
    op.drop_index("idx_aff_map_product_id", table_name="affiliate_product_mappings")
    op.drop_index("idx_aff_map_network", table_name="affiliate_product_mappings")
    op.drop_table("affiliate_product_mappings")

    # ── affiliate_commissions ──────────────────────────────────────────
    op.drop_index("idx_aff_comm_updated_at", table_name="affiliate_commissions")
    op.drop_index("idx_aff_comm_earned_at", table_name="affiliate_commissions")
    op.drop_index("idx_aff_comm_buywhere_product_id", table_name="affiliate_commissions")
    op.drop_index("idx_aff_comm_network_product_id", table_name="affiliate_commissions")
    op.drop_constraint("fk_aff_comm_buywhere_product", "affiliate_commissions", type_="foreignkey")
    op.drop_column("affiliate_commissions", "metadata")
    op.drop_column("affiliate_commissions", "updated_at")
    op.drop_column("affiliate_commissions", "received_at")
    op.drop_column("affiliate_commissions", "earned_at")
    op.drop_column("affiliate_commissions", "status_history")
    op.drop_column("affiliate_commissions", "buywhere_product_id")
    op.drop_column("affiliate_commissions", "network_product_id")
