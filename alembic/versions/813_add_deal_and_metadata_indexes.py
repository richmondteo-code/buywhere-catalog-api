"""Add GIN index on metadata JSONB and partial index for deal-eligible products.

BUY-12002: get_deals was doing a full sequential scan (20s) because metadata->>'original_price'
had no index. This adds:
  1. A GIN index (jsonb_path_ops) on products.metadata for fast has_key lookups
  2. A partial B-tree index on (is_active, price) WHERE metadata ? 'original_price'
     for the deals query filter + sort

Revision ID: 813
Revises: 812
Create Date: 2026-05-05
"""
from alembic import op


revision = "813"
down_revision = "812"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_products_metadata_gin",
        "products",
        ["metadata"],
        postgresql_using="gin",
        postgresql_ops={"metadata": "jsonb_path_ops"},
    )
    op.create_index(
        "idx_products_deal_eligible",
        "products",
        ["is_active", "price"],
        postgresql_where="metadata ? 'original_price'",
    )


def downgrade() -> None:
    op.drop_index("idx_products_deal_eligible", table_name="products")
    op.drop_index("idx_products_metadata_gin", table_name="products")
