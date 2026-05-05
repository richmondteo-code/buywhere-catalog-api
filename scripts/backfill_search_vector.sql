-- Backfill search_vector and title_search_vector columns
-- Run against the production database to restore FTS functionality

UPDATE products
SET
    search_vector = to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, '')),
    title_search_vector = to_tsvector('english', coalesce(title, ''))
WHERE search_vector IS NULL
   OR title_search_vector IS NULL;

-- Verify backfill
DO $$
DECLARE
    total_products bigint;
    null_search bigint;
    null_title bigint;
BEGIN
    SELECT count(*) INTO total_products FROM products;
    SELECT count(*) INTO null_search FROM products WHERE search_vector IS NULL;
    SELECT count(*) INTO null_title FROM products WHERE title_search_vector IS NULL;

    RAISE NOTICE 'Products: %, NULL search_vector: %, NULL title_search_vector: %',
        total_products, null_search, null_title;
END $$;
