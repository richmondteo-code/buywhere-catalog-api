"""Add category_counts materialized view for instant list_categories queries.

BUY-12097: list_categories was doing a full GROUP BY on the products table
(4.2s). The materialized view pre-aggregates counts and is refreshed
periodically by a background task in main.py.

Revision ID: 814
Revises: 813
Create Date: 2026-05-05
"""
from alembic import op


revision = "814"
down_revision = "813"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE MATERIALIZED VIEW category_counts AS
        SELECT category, COUNT(*)::integer AS product_count
        FROM products
        WHERE is_active = TRUE AND category IS NOT NULL
        GROUP BY category
        ORDER BY product_count DESC
    """)
    op.create_index("idx_category_counts_category", "category_counts", ["category"], unique=True)


def downgrade() -> None:
    op.drop_index("idx_category_counts_category", table_name="category_counts")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS category_counts")
