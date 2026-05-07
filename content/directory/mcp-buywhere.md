---
title: "BuyWhere — MCP Server for AI Shopping Agents"
slug: "mcp-server-buywhere"
description: "BuyWhere is an MCP server and API for AI shopping agents that compares product prices across Amazon, Best Buy, Walmart, Shopee, Lazada and 500+ retailers in real-time. Built for Claude, Cursor, and any MCP-compatible AI agent."
category: "Developer Tools"
tags:
  - "MCP server"
  - "model context protocol"
  - "shopping agent"
  - "price comparison API"
  - "AI agent"
  - "product search"
  - "Claude"
  - "Cursor"
  - "Windsurf"
published: true
---

# BuyWhere — MCP Server for AI Shopping Agents

## Overview

BuyWhere provides a Model Context Protocol (MCP) server that gives AI agents real-time access to product pricing across 500+ retailers in the US and Singapore. AI agents can search products, compare prices, find the best deals, and track price changes — all through natural language commands.

## MCP Server Features

### Available Tools

| Tool | Description |
|------|-------------|
| `search_products` | Search products by query with country and category filters |
| `get_product` | Retrieve detailed product information by ID |
| `compare_prices` | Compare prices across all merchants for a specific product |
| `find_best_price` | Find the lowest price across all retailers |
| `get_merchant_info` | Get merchant details including rating, return policy, shipping |
| `track_price` | Monitor price changes for a product over time |

### Supported Regions

| Region | Currency | Retailers |
|--------|----------|-----------|
| United States | USD | Amazon, Best Buy, Walmart, Target, Costco, Newegg, B&H Photo |
| Singapore | SGD | Shopee, Lazada, Courteney |

## Installation

```bash
# Install via npm
npm install @buywhere/mcp-server

# Or install via Smithery
npx @smithery-ai/cli install @buywhere/mcp-server
```

## Configuration

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

## Usage Example

```typescript
// Search for products
const results = await mcp.buywhere.search_products({
  query: "Sony WH-1000XM5",
  country: "us",
  limit: 5
});

// Compare prices across retailers
const prices = await mcp.buywhere.compare_prices({
  product_id: results.items[0].id,
  country: "us"
});

// Find the best price
const best = await mcp.buywhere.find_best_price({
  product_id: results.items[0].id,
  country: "us"
});
```

## API Response Format

```json
{
  "items": [
    {
      "id": "12345",
      "name": "Sony WH-1000XM5 Wireless Headphones",
      "price": 349.99,
      "currency": "USD",
      "merchant": "Amazon",
      "url": "https://amazon.com/dp/...",
      "in_stock": true,
      "rating": 4.8
    }
  ],
  "total": 45,
  "page": 1
}
```

## Use Cases

### AI Shopping Assistants
Build AI agents that recommend products and show live prices from multiple retailers.

### Deal Alert Systems
Monitor price changes and notify users when products hit target prices.

### Price Comparison Dashboards
Create comparison UIs showing prices across multiple retailers in real-time.

### Affiliate Marketing
Generate affiliate links with live pricing data for monetized shopping content.

## Pricing

| Plan | Price | API Calls | MCP Tools |
|------|-------|-----------|-----------|
| Free | $0 | 1,000/month | search_products, get_product |
| Developer | $29 | 50,000/month | All tools + price history |
| Business | $99 | 500,000/month | All tools + priority support |

## Related Documentation

- [API Reference](/pages/api-reference)
- [Developer Documentation](/developers)
- [BuyWhere vs Smithery Alternatives](/compare/buywhere-vs-smithery-alternatives)
- [BuyWhere MCP Developer FAQ](/compare/buywhere-mcp-developer-faq)
