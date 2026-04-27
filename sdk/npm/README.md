# @buywhere/sdk

Official TypeScript SDK for [BuyWhere](https://buywhere.ai) — the agent-native product catalog API for AI agent commerce in Singapore and globally.

## Installation

```bash
npm install @buywhere/sdk
```

Requires Node.js 18 or later.

## Quick Start

```typescript
import { BuyWhereClient } from "@buywhere/sdk";

const client = new BuyWhereClient(process.env.BUYWHERE_API_KEY!);

const results = await client.search({
  q: "wireless headphones",
  limit: 5,
  in_stock: true,
});

console.log(`Found ${results.total} products`);
for (const product of results.items) {
  console.log(`${product.name} | ${product.currency} ${product.price} | ${product.source}`);
}
```

Set your API key before running examples:

```bash
export BUYWHERE_API_KEY="bw_live_your_key_here"
```

Or pass it directly:

```typescript
const client = new BuyWhereClient("bw_live_your_key_here");
```

## Usage Examples

### Search and fetch a product

```typescript
import { BuyWhereClient } from "@buywhere/sdk";

const client = new BuyWhereClient(process.env.BUYWHERE_API_KEY!);

const results = await client.search({
  q: "vitamin c serum",
  category: "Health & Beauty",
  limit: 10,
  in_stock: true,
});

const first = results.items[0];
if (!first) {
  throw new Error("No matching products found");
}

console.log("Top match:", first.name, first.price, first.currency);

const product = await client.getProduct(first.id);
console.log("Buy URL:", product.affiliate_url ?? product.buy_url);
```

### Compare merchants for a known product

```typescript
import { BuyWhereClient } from "@buywhere/sdk";

const client = new BuyWhereClient(process.env.BUYWHERE_API_KEY!);

const search = await client.search({ q: "Nintendo Switch OLED", limit: 1 });
const product = search.items[0];

if (!product) {
  throw new Error("Product not found");
}

const comparison = await client.compare({ product_id: product.id });

console.log(`Compared ${comparison.total_matches} listings for ${comparison.source_product_name}`);

for (const match of comparison.matches.slice(0, 5)) {
  console.log(`${match.source}: ${match.currency} ${match.price}`);
}

if (comparison.highlights?.cheapest) {
  console.log(
    "Cheapest:",
    comparison.highlights.cheapest.source,
    comparison.highlights.cheapest.price
  );
}
```

### Track deals feed

```typescript
import { BuyWhereClient } from "@buywhere/sdk";

const client = new BuyWhereClient(process.env.BUYWHERE_API_KEY!);

const deals = await client.getDeals({
  category: "Electronics",
  min_discount_pct: 25,
  limit: 20,
});

for (const deal of deals.items) {
  console.log(`${deal.name} dropped ${deal.discount_pct}% to ${deal.currency} ${deal.price}`);
}
```

### Resolve the final outbound URL

```typescript
import { BuyWhereClient } from "@buywhere/sdk";

const client = new BuyWhereClient(process.env.BUYWHERE_API_KEY!);

const resolved = await client.resolveAffiliate(78234, { trackClick: true });
console.log(resolved.resolved_url);
```

### Subscribe to new deals

```typescript
import { BuyWhereClient } from "@buywhere/sdk";

const client = new BuyWhereClient(process.env.BUYWHERE_API_KEY!);

const { stop } = await client.subscribe(
  (deal) => console.log("New deal:", deal.name),
  { category: "Health & Beauty", min_discount_pct: 30 },
  60000
);

setTimeout(() => stop(), 5 * 60 * 1000);
```

### Runnable repo examples

The repository includes runnable scripts in `sdk/npm/examples`:

```bash
npm install
npm run example:search -- "mechanical keyboard"
npm run example:get-product -- 78234
npm run example:compare -- "Nintendo Switch OLED"
npm run example:price-history -- "iPhone 15" 30
BUYWHERE_WEBHOOK_URL="https://example.com/webhooks/buywhere" npm run example:webhook
```

`example:price-history` and `example:webhook` use raw HTTP for now because the current TypeScript client does not yet expose dedicated helper methods for those endpoints.

## API Reference

### `new BuyWhereClient(apiKey, options?)`

Create a new client instance.

| Option | Type | Default |
|--------|------|---------|
| `baseUrl` | `string` | `https://api.buywhere.ai` |
| `timeout` | `number` | `30000` |
| `maxRetries` | `number` | `3` |
| `retryDelay` | `number` | `1000` |
| `backoffMultiplier` | `number` | `2` |

### Methods

#### `search(options?)`
Search for products.

```typescript
const results = await client.search({
  q: "query string",
  category: "Health",
  min_price: 10,
  max_price: 100,
  source: "guardian_sg",
  in_stock: true,
  limit: 20,
  offset: 0,
});
```

Returns `ProductListResponse` with `total`, `limit`, `offset`, `has_more`, and `items`.

#### `getProduct(productId)`
Get a single product by ID.

```typescript
const product = await client.getProduct(12345);
```

#### `resolveAffiliate(productId, options?)`
Resolve the best outbound URL for a product, optionally recording a tracked click.

```typescript
const resolved = await client.resolveAffiliate(12345, { trackClick: true });
console.log(resolved.resolved_url);
```

#### `compare(options)`
Compare a product across merchants.

```typescript
const comparison = await client.compare({
  product_id: 12345,
  min_price: 10,
  max_price: 100,
});
```

#### `compareSearch(options)`
Search for comparable listings without looking up a product ID first.

```typescript
const comparison = await client.compareSearch({
  q: "Dyson V12 cordless vacuum",
  limit: 10,
});
```

#### `compareProductById(productId, options?)`
Compare a product with the `/v1/compare/{productId}` endpoint.

```typescript
const comparison = await client.compareProductById(12345, {
  min_price: 50,
  max_price: 500,
});
```

#### `compareProducts(options)`
Compare multiple products at once.

```typescript
const matrix = await client.compareProducts({
  product_ids: [123, 456, 789],
  min_price: 10,
  max_price: 100,
});
```

#### `compareProductsDiff(options)`
Get detailed diff between products.

```typescript
const diff = await client.compareProductsDiff({
  product_ids: [123, 456],
  include_image_similarity: true,
});
```

#### `getDeals(options?)`
Get current deals/discounts.

```typescript
const deals = await client.getDeals({
  category: "Health",
  min_discount_pct: 30,
  limit: 50,
});
```

#### `trending(period?, category?, limit?)`
Get trending products.

```typescript
const trending = await client.trending("7d", "Skin Care", 50);
```

#### `categories()`
Get all available categories.

```typescript
const { categories } = await client.categories();
```

#### `changelog()`
Fetch recent API release notes.

```typescript
const changelog = await client.changelog();
console.log(changelog.releases[0]?.version);
```

#### `ingest(request)`
Ingest products into the catalog (for merchants).

```typescript
await client.ingest({
  source: "my_store",
  products: [{ sku: "ABC123", title: "Product", price: 29.99, url: "https://..." }],
});
```

#### `exportProducts(options?)`
Export products in CSV or JSON format.

```typescript
const csv = await client.exportProducts({ format: "csv", category: "Health" });
```

#### `subscribe(callback, options?, intervalMs?)`
Subscribe to new deals with a callback. Returns a stop function.

```typescript
const { stop } = await client.subscribe(
  (deal) => console.log(deal.name),
  { min_discount_pct: 50 },
  60000 // poll every 60s
);
```

#### `health()`
Check API health status.

```typescript
const status = await client.health();
```

#### `apiInfo()`
Get API version and endpoint info.

```typescript
const info = await client.apiInfo();
```

### Error Handling

```typescript
import {
  BuyWhereClient,
  AuthenticationError,
  RateLimitError,
  NotFoundError,
  ValidationError,
  ServerError,
} from "@buywhere/sdk";

const client = new BuyWhereClient(process.env.BUYWHERE_API_KEY!);

try {
  const product = await client.getProduct(999999);
} catch (error) {
  if (error instanceof NotFoundError) {
    console.log("Product not found");
  } else if (error instanceof RateLimitError) {
    console.log("Rate limited, retry later");
  } else if (error instanceof AuthenticationError) {
    console.log("Invalid API key");
  } else if (error instanceof ValidationError) {
    console.log("Request validation failed");
  } else if (error instanceof ServerError) {
    console.log("BuyWhere is unavailable, retry later");
  }
}
```

## Common Patterns

### Run from a Node script

```bash
node --env-file=.env --input-type=module <<'EOF'
import { BuyWhereClient } from "@buywhere/sdk";

const client = new BuyWhereClient(process.env.BUYWHERE_API_KEY);
const results = await client.search({ q: "mechanical keyboard", limit: 3 });

for (const item of results.items) {
  console.log(`${item.name} -> ${item.currency} ${item.price}`);
}
EOF
```

### Use in a Next.js route handler

```typescript
import { BuyWhereClient } from "@buywhere/sdk";
import { NextResponse } from "next/server";

const client = new BuyWhereClient(process.env.BUYWHERE_API_KEY!);

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const q = searchParams.get("q") ?? "";

  const results = await client.search({ q, limit: 10 });
  return NextResponse.json(results);
}
```

## License

MIT
