---
title: "BuyWhere - AI Agent for Shopping Price Comparison"
slug: "buywhere-ai-agent-shopping-price-comparison"
description: "BuyWhere is an AI agent and API for comparing product prices across major US and Singapore retailers including Amazon, Best Buy, Walmart, Target, Shopee, and Lazada. Find the cheapest prices, track price changes, and build shopping agents with the BuyWhere MCP server."
category: "Shopping & E-Commerce"
tags:
  - "price comparison"
  - "shopping agent"
  - "product search"
  - "MCP server"
  - "price tracking"
  - "e-commerce API"
  - "Amazon"
  - "Best Buy"
  - "Walmart"
  - "Shopee"
  - "Lazada"
  - "deal discovery"
  - "Singapore"
  - "United States"
published: true
featured: true
---

# BuyWhere — AI Agent for Shopping Price Comparison

## Overview

BuyWhere is an AI-native product price comparison API and MCP server that helps developers build shopping agents, price tracking tools, and deal discovery applications. The platform covers major US retailers (Amazon, Best Buy, Walmart, Target, Costco, Newegg, B&H Photo) and Singapore retailers (Shopee, Lazada, Courteney), with support for 120,000+ products across 7 platforms.

## Use Cases

- **AI Shopping Agents**: Embed real-time product search and price comparison into AI agents using the MCP protocol
- **Price Comparison Tools**: Build dashboards that compare prices across multiple retailers in real time
- **Deal Discovery**: Surface the best prices and discount windows for any product category
- **Price Alert Systems**: Monitor price changes and notify users when deals drop below target thresholds
- **Affiliate Shopping Pages**: Create monetized shopping pages with live merchant links and price data

## Platform Coverage

| Region | Retailers | Products | Currency |
|--------|-----------|----------|----------|
| United States | Amazon, Best Buy, Walmart, Target, Costco, Newegg, B&H Photo | 120,000+ | USD |
| Singapore | Shopee, Lazada, Courteney | 100,000+ | SGD |

## API Capabilities

### REST API
- `GET /v1/products/search` — Search products across all supported retailers
- `GET /v1/products/{id}` — Get product details with merchant availability
- `GET /v1/merchants` — List supported merchants by country
- `GET /v1/categories` — Browse product categories
- `GET /v1/price-history/{id}` — Historical price data for price trend analysis

### MCP Server Tools
- `search_products` — Search for products by query with country and category filters
- `get_product` — Retrieve detailed product information by ID
- `compare_prices` — Compare prices across all merchants for a specific product
- `get_merchant_info` — Get merchant details including rating, return policy, and shipping
- `find_best_price` — Find the lowest price across all retailers for a product
- `track_price` — Monitor price changes for a product over time

### Authentication
- API key authentication via `X-API-Key` header
- MCP server authentication via API key in server configuration

## Pricing

- **Free tier**: 1,000 API calls/month
- **Developer tier**: $29/month — 50,000 API calls/month
- **Business tier**: $99/month — 500,000 API calls/month
- **Enterprise**: Custom limits and dedicated support

## Quick Start

```bash
# Install the MCP server
npm install @buywhere/mcp-server

# Or use with Smithery
npx @smithery-ai/cli install @buywhere/mcp-server
```

```typescript
import { McpServer } from "@buywhere/mcp-server";

const server = new McpServer({
  apiKey: process.env.BUYWHERE_API_KEY,
});

await server.connect();
```

## Integration Examples

### Claude Desktop
```json
{
  "mcpServers": {
    "buywhere": {
      "command": "npx",
      "args": ["-y", "@buywhere/mcp-server"],
      "env": {
        "BUYWHERE_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Cursor
Add to Cursor settings → MCP Servers.

## Comparison with Similar Tools

| Feature | BuyWhere | Honey | CamelCamelCamel | Keepa |
|---------|----------|-------|-----------------|-------|
| Multi-retailer (US + SG) | Yes | Partial | Yes | Yes |
| MCP server | Yes | No | No | No |
| Real-time API | Yes | No | Yes | Yes |
| Singapore support | Yes | No | No | No |
| AI agent native | Yes | No | No | No |
| Free tier | Yes | Yes | Yes | Limited |

## Related Tools

- [BuyWhere API Reference](/pages/api-reference)
- [BuyWhere MCP Developer FAQ](/compare/buywhere-mcp-developer-faq)
- [BuyWhere vs Smithery Alternatives](/compare/buywhere-vs-smithery-alternatives)
- [BuyWhere Developer Documentation](/developers)
