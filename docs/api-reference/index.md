# API Reference

Complete reference for all BuyWhere API endpoints.

## Base URL

```
https://api.buywhere.ai
```

## Authentication

All endpoints require a Bearer token:

```
Authorization: Bearer bw_live_xxxxx
```

See the [Authentication Guide](../guides/authentication.md) for details.

## Table of Contents

- [Search Products](#search-products)
- [Get Product by ID](#get-product-by-id)
- [Best Price](#best-price)
- [Compare Products](#compare-products)
- [Compare Matrix](#compare-matrix)
- [Compare Diff](#compare-diff)
- [Trending Products](#trending-products)
- [Categories](#categories)
- [Export Products](#export-products)
- [Deals](#deals)
- [API Root](#api-root)
- [Health Check](#health-check)

---

## Search Products

Full-text search across all products.

```
GET /v1/search
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | No | Full-text search query |
| `category` | string | No | Filter by category name (case-insensitive partial match) |
| `min_price` | number | No | Minimum price filter (SGD) |
| `max_price` | number | No | Maximum price filter (SGD) |
| `platform` | string | No | Filter by source platform (e.g., `lazada_sg`, `shopee_sg`) |
| `in_stock` | boolean | No | Filter by availability |
| `limit` | integer | No | Results per page (1-100, default: 20) |
| `offset` | integer | No | Pagination offset (default: 0) |

### Example

```bash
curl "https://api.buywhere.ai/v1/search?q=dyson%20vacuum&limit=10" \
  -H "Authorization: Bearer bw_live_xxxxx"
```

### Response

```json
{
  "total": 142,
  "limit": 10,
  "offset": 0,
  "has_more": true,
  "items": [
    {
      "id": 12345,
      "sku": "DY-VC7-XXXX",
      "source": "lazada_sg",
      "merchant_id": "LAZADA_SG_001",
      "name": "Dyson V15 Detect Vacuum Cleaner",
      "description": "Laser detects microscopic dust...",
      "price": "749.00",
      "currency": "SGD",
      "buy_url": "https://www.lazada.sg/products/...",
      "affiliate_url": "https://buywhere.ai/track/...",
      "image_url": "https://...jpg",
      "brand": "Dyson",
      "category": "Vacuum Cleaners",
      "category_path": ["Home & Garden", "Cleaning", "Vacuum Cleaners"],
      "rating": "4.8",
      "is_available": true,
      "last_checked": "2026-04-03T12:00:00Z",
      "metadata": null,
      "updated_at": "2026-04-03T14:30:00Z"
    }
  ]
}
```

---

## Get Product by ID

Retrieve a single product by its BuyWhere ID.

```
GET /v1/products/{product_id}
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `product_id` | integer | The BuyWhere product ID |

### Example

```bash
curl "https://api.buywhere.ai/v1/products/12345" \
  -H "Authorization: Bearer bw_live_xxxxx"
```

### Response

Returns a single `Product` object. See [Product Schema](#product-schema).

---

## Best Price

Find the cheapest listing for a product across all platforms.

```
GET /v1/products/best-price
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Product name to search for |
| `category` | string | No | Optional category filter |

### Example

```bash
curl "https://api.buywhere.ai/v1/products/best-price?q=nintendo%20switch%20oled" \
  -H "Authorization: Bearer bw_live_xxxxx"
```

### Response

Returns a single `Product` object — the cheapest match.

### Error Responses

| Status | Description |
|--------|-------------|
| 404 | No products found for the query |

---

## Compare Products

Find all listings of the same product across platforms.

```
GET /v1/products/compare
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | integer | Yes | Source product ID to find matches for |
| `min_price` | number | No | Minimum price filter for matches |
| `max_price` | number | No | Maximum price filter for matches |

### Example

```bash
curl "https://api.buywhere.ai/v1/products/compare?product_id=12345" \
  -H "Authorization: Bearer bw_live_xxxxx"
```

### Response

```json
{
  "source_product_id": 12345,
  "source_product_name": "Dyson V15 Detect Vacuum Cleaner",
  "matches": [
    {
      "id": 12346,
      "sku": "DY-VC7-YYY",
      "source": "shopee_sg",
      "merchant_id": "SHOPEE_SG_002",
      "name": "Dyson V15 Detect Vacuum Cleaner",
      "price": "729.00",
      "currency": "SGD",
      "buy_url": "https://shopee.sg/...",
      "affiliate_url": "https://buywhere.ai/track/...",
      "match_score": 0.95,
      ...
    }
  ],
  "total_matches": 5
}
```

---

## Compare Matrix

Compare multiple products across platforms in a single request.

```
POST /v1/products/compare
```

### Request Body

```json
{
  "product_ids": [12345, 67890, 11111],
  "min_price": 0,
  "max_price": 10000
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `product_ids` | array[integer] | Yes | List of 2-20 product IDs |
| `min_price` | number | No | Minimum price filter |
| `max_price` | number | No | Maximum price filter |

### Response

```json
{
  "comparisons": [
    {
      "source_product_id": 12345,
      "source_product_name": "Product A",
      "matches": [...],
      "total_matches": 5
    }
  ],
  "total_products": 3
}
```

---

## Compare Diff

Compare 2-5 products directly — returns structured field differences.

```
POST /v1/products/compare/diff
```

### Request Body

```json
{
  "product_ids": [12345, 67890, 11111],
  "include_image_similarity": false
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `product_ids` | array[integer] | Yes | List of 2-5 product IDs |
| `include_image_similarity` | boolean | No | Include image similarity computation |

### Response

```json
{
  "products": [
    {
      "id": 12345,
      "name": "Product A",
      "price": "749.00",
      "price_rank": 2,
      ...
    }
  ],
  "field_diffs": [
    {
      "field": "price",
      "values": ["749.00", "729.00", "799.00"],
      "all_identical": false
    }
  ],
  "identical_fields": ["brand", "category"],
  "cheapest_product_id": 67890,
  "most_expensive_product_id": 11111,
  "price_spread": "70.00",
  "price_spread_pct": 9.61
}
```

---

## Trending Products

Get recently updated products by category.

```
GET /v1/products/trending
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | No | Filter by category name |
| `limit` | integer | No | Number of products (1-100, default: 50) |

### Example

```bash
curl "https://api.buywhere.ai/v1/products/trending?category=Electronics&limit=20" \
  -H "Authorization: Bearer bw_live_xxxxx"
```

---

## Categories

List all available product categories with item counts.

```
GET /v1/categories
```

### Example

```bash
curl "https://api.buywhere.ai/v1/categories" \
  -H "Authorization: Bearer bw_live_xxxxx"
```

### Response

```json
{
  "categories": [
    {"name": "Electronics", "count": 125000},
    {"name": "Fashion", "count": 98000},
    {"name": "Home & Garden", "count": 67000}
  ],
  "total": 45
}
```

---

## Export Products

Export products as CSV or JSON.

```
GET /v1/products/export
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `format` | string | No | Export format: `csv` or `json` (default: `json`) |
| `category` | string | No | Filter by category |
| `source` | string | No | Filter by source platform |
| `min_price` | number | No | Minimum price |
| `max_price` | number | No | Maximum price |
| `limit` | integer | No | Max records (1-10000, default: 1000) |
| `offset` | integer | No | Pagination offset (default: 0) |

### Example

```bash
curl "https://api.buywhere.ai/v1/products/export?format=csv&limit=100" \
  -H "Authorization: Bearer bw_live_xxxxx"
```

---

## Deals

Get products currently priced below their historical price.

```
GET /v1/deals
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | No | Filter by category |
| `min_discount_pct` | number | No | Minimum discount % (default: 10) |
| `limit` | integer | No | Results per page (1-100, default: 20) |
| `offset` | integer | No | Pagination offset (default: 0) |

---

## API Root

Get API metadata and available endpoints.

```
GET /v1
```

### Response

```json
{
  "api": "BuyWhere Catalog API",
  "version": "v1",
  "endpoints": {
    "search": "GET /v1/search",
    "products": "GET /v1/products",
    "best_price": "GET /v1/products/best-price",
    "compare_single": "GET /v1/products/compare",
    "compare_matrix": "POST /v1/products/compare",
    "compare_diff": "POST /v1/products/compare/diff",
    "trending": "GET /v1/products/trending",
    "export": "GET /v1/products/export?format=csv|json",
    "product": "GET /v1/products/{id}",
    "categories": "GET /v1/categories",
    "deals": "GET /v1/deals"
  },
  "auth": "Bearer token required (API key)",
  "docs": "/docs"
}
```

---

## Health Check

Check API health status.

```
GET /health
```

### Response

```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "production"
}
```

---

## Product Schema

All product-related endpoints return objects conforming to this schema:

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | BuyWhere product ID |
| `sku` | string | Product SKU |
| `source` | string | Source platform (e.g., `lazada_sg`, `shopee_sg`) |
| `merchant_id` | string | Merchant/shop identifier |
| `name` | string | Product title |
| `description` | string | Product description |
| `price` | string | Price as decimal string |
| `currency` | string | Currency code (e.g., `SGD`) |
| `buy_url` | string | Direct purchase URL |
| `affiliate_url` | string | Tracked affiliate URL |
| `image_url` | string | Product image URL |
| `brand` | string | Brand name |
| `category` | string | Primary category |
| `category_path` | array[string] | Full category hierarchy |
| `rating` | string | Product rating |
| `is_available` | boolean | Currently in stock |
| `last_checked` | datetime | Last availability check |
| `metadata` | any | Additional metadata |
| `updated_at` | datetime | Last update timestamp |

---

## Error Codes

| Status | Meaning |
|--------|---------|
| 400 | Bad Request — Invalid parameters |
| 401 | Unauthorized — Invalid or missing API key |
| 403 | Forbidden — Invalid admin secret |
| 404 | Not Found — Resource doesn't exist |
| 422 | Validation Error — Request validation failed |
| 429 | Rate Limit Exceeded — Slow down requests |
| 500 | Server Error — Something went wrong on our end |
| 503 | Service Unavailable — Temporary outage |