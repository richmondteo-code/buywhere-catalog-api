"""
BuyWhere MCP Server (BUY-347)

Exposes the BuyWhere product catalog to AI agents via the Model Context
Protocol (MCP). Implements:
  - search_products   — keyword search across all platforms
  - get_product       — retrieve a specific product by ID
  - find_best_price   — find cheapest listing for a product name
  - get_deals         — find discounted products

Run with:
  python mcp_server.py

Configure via environment variables:
  BUYWHERE_API_KEY  — your BuyWhere API key (required)
  BUYWHERE_API_URL  — base URL (default: http://localhost:8000)
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE_URL = os.environ.get("BUYWHERE_API_URL", "http://localhost:8000")
API_KEY = os.environ.get("BUYWHERE_API_KEY", "")
DEFAULT_LIMIT = 10

if not API_KEY:
    logger.warning("BUYWHERE_API_KEY is not set — requests may be rejected")

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

server = Server("buywhere")


@server.list_tools()
async def list_tools() -> ListToolsResult:
    return ListToolsResult(
        tools=[
            Tool(
                name="search_products",
                description=(
                    "Search the BuyWhere product catalog by keyword. "
                    "Returns ranked results from Singapore e-commerce platforms "
                    "(Lazada, Shopee, Qoo10, Carousell)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Product search query."},
                        "category": {"type": "string", "description": "Optional category filter."},
                        "min_price": {"type": "number", "description": "Minimum price in SGD."},
                        "max_price": {"type": "number", "description": "Maximum price in SGD."},
                        "source": {
                            "type": "string",
                            "description": "Platform filter (lazada_sg, shopee_sg, etc.).",
                        },
                        "limit": {
                            "type": "integer",
                            "description": f"Max results (default {DEFAULT_LIMIT}, max 50).",
                            "default": DEFAULT_LIMIT,
                            "minimum": 1,
                            "maximum": 50,
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="get_product",
                description="Retrieve full details for a specific product by its BuyWhere ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "integer",
                            "description": "The BuyWhere product ID.",
                        },
                    },
                    "required": ["product_id"],
                },
            ),
            Tool(
                name="find_best_price",
                description=(
                    "Find the single cheapest listing for a product across all Singapore "
                    "e-commerce platforms. Returns the platform, price, and affiliate URL "
                    "for the lowest available price."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "product_name": {
                            "type": "string",
                            "description": "Product name or search query.",
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional category to narrow the search.",
                        },
                    },
                    "required": ["product_name"],
                },
            ),
            Tool(
                name="get_deals",
                description=(
                    "Find products with significant price drops compared to their original "
                    "price. Returns deals sorted by discount percentage with current price, "
                    "original price, and savings."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Optional category filter (e.g. 'electronics').",
                        },
                        "min_discount_pct": {
                            "type": "number",
                            "description": "Minimum discount percentage (default 10).",
                            "default": 10,
                            "minimum": 0,
                            "maximum": 100,
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max results (default 10, max 50).",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50,
                        },
                    },
                    "required": [],
                },
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    if name == "search_products":
        return await _handle_search_products(arguments)
    if name == "get_product":
        return await _handle_get_product(arguments)
    if name == "find_best_price":
        return await _handle_find_best_price(arguments)
    if name == "get_deals":
        return await _handle_get_deals(arguments)
    return CallToolResult(
        content=[TextContent(type="text", text=f"Unknown tool: {name}")],
        isError=True,
    )


async def _handle_search_products(args: dict[str, Any]) -> CallToolResult:
    query = str(args.get("query", "")).strip()
    if not query:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: query is required")],
            isError=True,
        )
    params: dict[str, Any] = {"q": query, "limit": min(int(args.get("limit", DEFAULT_LIMIT)), 50)}
    for key in ("category", "min_price", "max_price", "source"):
        if args.get(key) is not None:
            params[key] = args[key]

    try:
        data = await _api_get("/v1/products", params)
    except Exception as exc:
        logger.exception("search_products API error for %r", query)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Search failed: {exc}")],
            isError=True,
        )

    items = data.get("items", []) if isinstance(data, dict) else []
    if not items:
        return CallToolResult(
            content=[TextContent(type="text", text=f"No products found for: {query}")]
        )

    lines = [f"Found {len(items)} product(s) for **{query}**:\n"]
    for i, p in enumerate(items, 1):
        lines.append(_fmt_product_summary(i, p))
    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])


async def _handle_get_product(args: dict[str, Any]) -> CallToolResult:
    product_id = args.get("product_id")
    if not product_id:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: product_id is required")],
            isError=True,
        )
    try:
        data = await _api_get(f"/v1/products/{product_id}")
    except Exception as exc:
        logger.exception("get_product API error for id %r", product_id)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Fetch failed: {exc}")],
            isError=True,
        )
    return CallToolResult(content=[TextContent(type="text", text=_fmt_product_detail(data))])


async def _handle_find_best_price(args: dict[str, Any]) -> CallToolResult:
    product_name = str(args.get("product_name", "")).strip()
    if not product_name:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: product_name is required")],
            isError=True,
        )
    params: dict[str, Any] = {"q": product_name}
    if args.get("category"):
        params["category"] = args["category"]

    try:
        p = await _api_get("/v1/products/best-price", params)
    except Exception as exc:
        logger.exception("find_best_price API error for %r", product_name)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Search failed: {exc}")],
            isError=True,
        )

    if not p or not isinstance(p, dict):
        return CallToolResult(
            content=[TextContent(type="text", text=f"No products found for: {product_name}")]
        )

    price_str = _fmt_price(p.get("price"), p.get("currency", "SGD"))
    affiliate = p.get("affiliate_url") or p.get("buy_url") or ""
    lines = [
        f"## Best Price: {p.get('name', 'Unknown')}",
        f"**Platform:** {p.get('source', 'unknown')}",
        f"**Price:** {price_str}",
        f"**Category:** {p.get('category') or 'N/A'}",
    ]
    if affiliate:
        lines.append(f"**Affiliate URL:** {affiliate}")
    lines.append(f"**Product ID:** {p.get('id', '')}")
    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])


async def _handle_get_deals(args: dict[str, Any]) -> CallToolResult:
    min_discount_pct = float(args.get("min_discount_pct", 10))
    limit = min(int(args.get("limit", DEFAULT_LIMIT)), 50)
    params: dict[str, Any] = {"min_discount_pct": min_discount_pct, "limit": limit}
    if args.get("category"):
        params["category"] = args["category"]

    try:
        data = await _api_get("/v1/deals", params)
    except Exception as exc:
        logger.exception("get_deals API error")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Deals fetch failed: {exc}")],
            isError=True,
        )

    items = data.get("items", []) if isinstance(data, dict) else []
    if not items:
        return CallToolResult(
            content=[TextContent(type="text", text=f"No deals found with ≥{min_discount_pct}% discount.")]
        )

    lines = [f"Found {len(items)} deal(s) with ≥{min_discount_pct}% discount:\n"]
    for i, d in enumerate(items, 1):
        current = _fmt_price(d.get("price"), d.get("currency", "SGD"))
        original = _fmt_price(d.get("original_price"), d.get("currency", "SGD")) if d.get("original_price") else "N/A"
        discount = d.get("discount_pct", 0) or 0
        lines.append(
            f"{i}. **{d.get('name', 'Unknown')}**\n"
            f"   Current: {current} | Was: {original} | Discount: {discount}%\n"
            f"   Platform: {d.get('source', 'unknown')} | ID: {d.get('id', '')}\n"
        )
    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

_headers: dict[str, str] = {"Accept": "application/json"}
if API_KEY:
    _headers["Authorization"] = f"Bearer {API_KEY}"


async def _api_get(path: str, params: dict[str, Any] | None = None) -> Any:
    async with httpx.AsyncClient(base_url=API_BASE_URL, headers=_headers, timeout=10.0) as client:
        resp = await client.get(path, params=params or {})
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_price(price: Any, currency: str = "SGD") -> str:
    if price is None:
        return "N/A"
    try:
        return f"{currency} {float(price):.2f}"
    except (TypeError, ValueError):
        return str(price)


def _fmt_product_summary(index: int, p: dict[str, Any]) -> str:
    name = p.get("name") or p.get("title") or "Unknown"
    price = _fmt_price(p.get("price"), p.get("currency", "SGD"))
    source = p.get("source", "unknown")
    pid = p.get("id", "")
    url = p.get("affiliate_url") or p.get("buy_url") or ""
    url_line = f"\n   URL: {url}" if url else ""
    return f"{index}. **{name}**\n   Price: {price} | Platform: {source}{url_line}\n   ID: {pid}\n"


def _fmt_product_detail(p: dict[str, Any]) -> str:
    if not isinstance(p, dict):
        return str(p)
    lines = [f"## {p.get('name') or 'Product'}"]
    for key, label in [
        ("id", "ID"),
        ("source", "Platform"),
        ("price", "Price"),
        ("currency", "Currency"),
        ("category", "Category"),
        ("affiliate_url", "Affiliate URL"),
        ("buy_url", "Buy URL"),
        ("image_url", "Image"),
    ]:
        val = p.get(key)
        if val is not None:
            lines.append(f"**{label}:** {val}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    logger.info("BuyWhere MCP server starting (API: %s)", API_BASE_URL)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
