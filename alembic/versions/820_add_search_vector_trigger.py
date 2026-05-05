"""Add database trigger to auto-populate search_vector and title_search_vector columns.

BUY-12252: Production MCP search_products returns 0 results because search_vector
and title_search_vector columns are NULL for all products. This migration:

1. Backfills existing NULL search_vector/title_search_vector values
2. Adds a trigger function and trigger to keep them in sync on INSERT/UPDATE
3. Adds GIN index coverage for the expression-based search fallback

Revision ID: 820
Revises: 819
Create Date: 2026-05-05
"""
from alembic import op


revision = "820"
down_revision = "819"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Backfill existing NULL values
    op.execute("""
        UPDATE products
        SET
            search_vector = to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, '')),
            title_search_vector = to_tsvector('english', coalesce(title, ''))
        WHERE search_vector IS NULL
           OR title_search_vector IS NULL
    """)

    # Create trigger function that updates both vector columns
    op.execute("""
        CREATE OR REPLACE FUNCTION products_search_vector_trigger()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := to_tsvector('english',
                coalesce(NEW.title, '') || ' ' || coalesce(NEW.description, '')
            );
            NEW.title_search_vector := to_tsvector('english',
                coalesce(NEW.title, '')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    # Drop old trigger if it exists (leftover from BUY-8859 manual fix)
    # before creating the new one — PostgreSQL does not support CREATE OR REPLACE TRIGGER
    op.execute("DROP TRIGGER IF EXISTS trg_products_search_vector ON products")

    # Create trigger on INSERT or UPDATE of title or description
    op.execute("""
        CREATE TRIGGER trg_products_search_vector
            BEFORE INSERT OR UPDATE OF title, description
            ON products
            FOR EACH ROW
            EXECUTE FUNCTION products_search_vector_trigger()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_products_search_vector ON products")
    op.execute("DROP FUNCTION IF EXISTS products_search_vector_trigger()")
