export const PRODUCT_LOOKUP_SELECT = `SELECT id, sku AS source_id, source AS domain, url,
        title, price, currency, image_url, metadata, updated_at,
        region, country_code, created_at, description, brand, mpn, gtin,
        category_path, category, merchant_id, avg_rating, review_count
 FROM products
 WHERE id::text = $1 OR canonical_id::text = $1 OR sku = $1
 ORDER BY CASE
   WHEN id::text = $1 THEN 0
   WHEN canonical_id::text = $1 THEN 1
   WHEN sku = $1 THEN 2
   ELSE 3
 END
 LIMIT 1`;

