# BuyWhere MCP Server

Agent-native product catalog API for Southeast Asia commerce. Search 1.5M+ products across Shopee, Lazada, Amazon, Walmart, and 20+ e-commerce platforms. Compare prices, find deals, browse categories.

[![Glama Score](https://glama.ai/mcp/servers/BuyWhere/buywhere/badges/score.svg)](https://glama.ai/mcp/servers/BuyWhere/buywhere)

## Installation

```bash
npx @buywhere/mcp-server
```

Or add to your MCP client config:

```json
{
  "mcpServers": {
    "buywhere": {
      "command": "npx",
      "args": ["@buywhere/mcp-server"],
      "env": {
        "BUYWHERE_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Remote MCP (HTTP/SSE)

```
https://api.buywhere.ai/mcp
```

Authentication: Bearer token (API key). Get a free key at [api.buywhere.ai/v1/auth/register](https://api.buywhere.ai/v1/auth/register).

## Tools

| Tool | Description |
|------|-------------|
| `search_products` | Full-text search across 1.5M+ products from 20+ platforms |
| `get_product` | Get full product details by BuyWhere product ID |
| `compare_prices` | Compare prices for a product across all platforms |
| `get_deals` | Find products with active discounts |
| `browse_categories` | Browse the product category taxonomy tree |
| `get_category_products` | Get products within a specific category |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BUYWHERE_API_KEY` | Yes | BuyWhere API key |
| `BUYWHERE_API_URL` | No | API base URL (default: `https://api.buywhere.ai`) |

## Documentation

Full API docs: [api.buywhere.ai/docs/guides/mcp](https://api.buywhere.ai/docs/guides/mcp)

## Links

- Homepage: [buywhere.ai](https://buywhere.ai)
- npm package: [@buywhere/mcp-server](https://www.npmjs.com/package/@buywhere/mcp-server)
- API: [api.buywhere.ai](https://api.buywhere.ai)

## License

MIT
