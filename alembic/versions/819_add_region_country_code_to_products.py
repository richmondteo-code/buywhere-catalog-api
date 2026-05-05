"""Add region and country_code columns to products table, backfill VN/TH data

Products from shopee_vn, shopee_th, and lazada_th scrapers had missing/wrong
region and country_code due to scrapers not setting these fields. They fell
back to DB defaults (region='sg', country_code='SG').

This migration:
1. Adds region and country_code columns if they don't exist (safe for prod
   where they may have been added via hotfix)
2. Creates geo/region indexes matching the model
3. Backfills correct values for VN/TH products

Revision ID: 819
Revises: 818
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa


revision = "819"
down_revision = "818"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Add columns safely (IF NOT EXISTS is available in PG 9.6+) ---
    op.execute(
        sa.text(
            "ALTER TABLE products "
            "ADD COLUMN IF NOT EXISTS region VARCHAR(10) NOT NULL DEFAULT 'sg'"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE products "
            "ADD COLUMN IF NOT EXISTS country_code VARCHAR(2) NOT NULL DEFAULT 'SG'"
        )
    )

    # --- Create indexes (IF NOT EXISTS, safe to re-run) ---
    op.execute(
        sa.text("CREATE INDEX IF NOT EXISTS idx_products_region ON products (region)")
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_products_country_code ON products (country_code)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_products_active_region "
            "ON products (is_active, region)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_products_active_region_price "
            "ON products (is_active, region, price)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_products_active_region_category "
            "ON products (is_active, region, category)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_products_active_region_available "
            "ON products (is_active, region, is_available)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_products_active_source_region "
            "ON products (is_active, source, region)"
        )
    )

    # --- Backfill VN/TH products ---
    op.execute(
        sa.text(
            "UPDATE products "
            "SET region = 'vn', country_code = 'VN' "
            "WHERE source = 'shopee_vn' "
            "  AND (region IS DISTINCT FROM 'vn' OR country_code IS DISTINCT FROM 'VN')"
        )
    )
    op.execute(
        sa.text(
            "UPDATE products "
            "SET region = 'th', country_code = 'TH' "
            "WHERE source = 'shopee_th' "
            "  AND (region IS DISTINCT FROM 'th' OR country_code IS DISTINCT FROM 'TH')"
        )
    )
    op.execute(
        sa.text(
            "UPDATE products "
            "SET region = 'th', country_code = 'TH' "
            "WHERE source = 'lazada_th' "
            "  AND (region IS DISTINCT FROM 'th' OR country_code IS DISTINCT FROM 'TH')"
        )
    )


def downgrade() -> None:
    # Drop composite indexes
    composite_indexes = [
        "idx_products_active_source_region",
        "idx_products_active_region_available",
        "idx_products_active_region_category",
        "idx_products_active_region_price",
        "idx_products_active_region",
    ]
    for idx in composite_indexes:
        op.drop_index(idx, table_name="products", if_exists=True)

    # Drop single-column indexes
    op.drop_index("idx_products_country_code", table_name="products", if_exists=True)
    op.drop_index("idx_products_region", table_name="products", if_exists=True)
