import logging
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.auth import get_current_api_key
from app.models.product import ApiKey

from mcp.server import Server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)

logger = logging.getLogger("mcp-http")

router = APIRouter(prefix="/mcp", tags=["mcp"])

_api_server: Server | None = None

_MCP_TOOLS = [
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
                "source": {"type": "string", "description": "Platform filter (lazada_sg, shopee_sg, etc.)."},
                "limit": {"type": "integer", "description": "Max results (default 10, max 50).", "default": 10, "minimum": 1, "maximum": 50},
                "filters": {
                    "type": "object",
                    "properties": {
                        "price_min": {"type": "number", "description": "Minimum price filter."},
                        "price_max": {"type": "number", "description": "Maximum price filter."},
                        "brand": {"type": "array", "items": {"type": "string"}, "description": "Brand filters (OR-combined)."},
                        "category": {"type": "string", "description": "Category filter."},
                        "in_stock": {"type": "boolean", "description": "In-stock only."},
                        "merchant": {"type": "string", "description": "Platform/source filter."},
                        "sort_by": {"type": "string", "enum": ["relevance", "price_asc", "price_desc", "newest"], "description": "Sort order."},
                    },
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
                "product_id": {"type": "integer", "description": "The BuyWhere product ID."},
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
                "product_name": {"type": "string", "description": "Product name or search query."},
                "category": {"type": "string", "description": "Optional category to narrow the search."},
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
                "category": {"type": "string", "description": "Optional category filter (e.g. 'electronics')."},
                "min_discount_pct": {"type": "number", "description": "Minimum discount percentage (default 10).", "default": 10, "minimum": 0, "maximum": 100},
                "limit": {"type": "integer", "description": "Max results (default 10, max 50).", "default": 10, "minimum": 1, "maximum": 50},
            },
            "required": [],
        },
    ),
    Tool(
        name="list_categories",
        description="Browse available product categories. Returns the category taxonomy and product counts.",
        inputSchema={
            "type": "object",
            "properties": {
                "parent_id": {"type": "integer", "description": "Parent category ID to get subcategories."},
            },
            "required": [],
        },
    ),
    Tool(
        name="compare_products",
        description="Side-by-side price comparison of products across platforms.",
        inputSchema={
            "type": "object",
            "properties": {
                "product_ids": {"type": "array", "items": {"type": "integer"}, "description": "Product IDs to compare."},
            },
            "required": ["product_ids"],
        },
    ),
]


def get_mcp_server() -> Server:
    global _api_server
    if _api_server is None:
        server = Server("buywhere")

        @server.list_tools()
        async def list_tools() -> ListToolsResult:
            return ListToolsResult(tools=_MCP_TOOLS)

        @server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
            handlers = {
                "search_products": _handle_search_products,
                "get_product": _handle_get_product,
                "find_best_price": _handle_find_best_price,
                "get_deals": _handle_get_deals,
                "list_categories": _handle_list_categories,
                "compare_products": _handle_compare_products,
            }
            handler = handlers.get(name)
            if handler is None:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                    isError=True,
                )
            result, _ = await handler(arguments)
            return result

        _api_server = server

    return _api_server


async def _handle_search_products(args: dict[str, Any]) -> tuple[CallToolResult, dict | None]:
    from unittest.mock import AsyncMock

    query = str(args.get("query", "")).strip()
    if not query:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: query is required")],
            isError=True,
        ), None

    # Build flat params from filters object + flat args
    params = {"q": query, "limit": min(int(args.get("limit", 10)), 50)}

    # Process structured filters
    filters = args.get("filters") or {}
    if isinstance(filters, dict):
        if filters.get("category") is not None:
            params["category"] = filters["category"]
        if filters.get("price_min") is not None:
            params["price_min"] = filters["price_min"]
        if filters.get("price_max") is not None:
            params["price_max"] = filters["price_max"]
        if filters.get("merchant") is not None:
            params["platform"] = filters["merchant"]
        if filters.get("in_stock") is not None:
            params["in_stock"] = str(filters["in_stock"]).lower()
        if filters.get("sort_by") is not None:
            params["sort_by"] = filters["sort_by"]
        # Brand: send as comma-separated for OR logic on backend
        if filters.get("brand"):
            params["brand"] = ",".join(filters["brand"])

    # Flat args as fallback (filters object wins on conflict)
    for key in ("category", "min_price", "max_price", "source"):
        if args.get(key) is not None and key not in params:
            params[key] = args[key]

    # Map flat args to backend params
    if "min_price" in params:
        params["price_min"] = params.pop("min_price")
    if "max_price" in params:
        params["price_max"] = params.pop("max_price")
    if "source" in params:
        params["platform"] = params.pop("source")

    try:
        data = await _api_get("/v1/products/search", params)
    except Exception as exc:
        logger.exception("search_products API error for %r", query)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Search failed: {exc}")],
            isError=True,
        ), None

    items = data.get("items", []) if isinstance(data, dict) else []
    if not items:
        msg = f"No products found for: {query}"
        # Include suggestion if provided by backend
        suggestion = data.get("suggestion") if isinstance(data, dict) else None
        if suggestion:
            msg += f"\nSuggestion: {suggestion}"
        return CallToolResult(content=[TextContent(type="text", text=msg)]), data

    lines = [f"Found {len(items)} product(s) for **{query}**:"]
    # Echo applied filters if provided
    applied = data.get("applied_filters") if isinstance(data, dict) else None
    if applied:
        lines.append(f"Filters applied: {applied}")
    lines.append("")
    for i, p in enumerate(items, 1):
        lines.append(_fmt_product_summary(i, p))
    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))]), data


async def _handle_get_product(args: dict[str, Any]) -> tuple[CallToolResult, dict | None]:
    product_id = args.get("product_id")
    if not product_id:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: product_id is required")],
            isError=True,
        ), None
    try:
        data = await _api_get(f"/v1/products/{product_id}")
    except Exception as exc:
        logger.exception("get_product API error for id %r", product_id)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Fetch failed: {exc}")],
            isError=True,
        ), None
    return CallToolResult(content=[TextContent(type="text", text=_fmt_product_detail(data))]), data


async def _handle_find_best_price(args: dict[str, Any]) -> tuple[CallToolResult, dict | None]:
    product_name = str(args.get("product_name", "")).strip()
    if not product_name:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: product_name is required")],
            isError=True,
        ), None
    params = {"q": product_name}
    if args.get("category"):
        params["category"] = args["category"]

    try:
        p = await _api_get("/v1/products/best-price", params)
    except Exception as exc:
        logger.exception("find_best_price API error for %r", product_name)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Search failed: {exc}")],
            isError=True,
        ), None

    if not p or not isinstance(p, dict):
        return CallToolResult(
            content=[TextContent(type="text", text=f"No products found for: {product_name}")]
        ), None

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
    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))]), p


async def _handle_get_deals(args: dict[str, Any]) -> tuple[CallToolResult, dict | None]:
    min_discount_pct = float(args.get("min_discount_pct", 10))
    limit = min(int(args.get("limit", 10)), 50)
    params = {"min_discount_pct": min_discount_pct, "limit": limit}
    if args.get("category"):
        params["category"] = args["category"]

    try:
        data = await _api_get("/v1/deals", params)
    except Exception as exc:
        logger.exception("get_deals API error")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Deals fetch failed: {exc}")],
            isError=True,
        ), None

    items = data.get("items", []) if isinstance(data, dict) else []
    if not items:
        return CallToolResult(
            content=[TextContent(type="text", text=f"No deals found with >={min_discount_pct}% discount.")]
        ), None

    lines = [f"Found {len(items)} deal(s) with >={min_discount_pct}% discount:\n"]
    for i, d in enumerate(items, 1):
        current = _fmt_price(d.get("price"), d.get("currency", "SGD"))
        original = _fmt_price(d.get("original_price"), d.get("currency", "SGD")) if d.get("original_price") else "N/A"
        discount = d.get("discount_pct", 0) or 0
        lines.append(
            f"{i}. **{d.get('name', 'Unknown')}**\n"
            f"   Current: {current} | Was: {original} | Discount: {discount}%\n"
            f"   Platform: {d.get('source', 'unknown')} | ID: {d.get('id', '')}\n"
        )
    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))]), data


async def _handle_list_categories(args: dict[str, Any]) -> tuple[CallToolResult, dict | None]:
    params = {}
    if args.get("parent_id") is not None:
        params["parent_id"] = args["parent_id"]
    try:
        data = await _api_get("/v1/categories", params)
    except Exception as exc:
        logger.exception("list_categories API error")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Categories fetch failed: {exc}")],
            isError=True,
        ), None
    categories = data.get("categories", []) if isinstance(data, dict) else []
    total = data.get("total", len(categories)) if isinstance(data, dict) else 0
    if not categories:
        return CallToolResult(
            content=[TextContent(type="text", text="No categories found.")]
        ), None
    lines = [f"Found {total} categor{'ies' if total != 1 else 'y'}:\n"]
    for c in categories:
        name = c.get("name") or c.get("category") or "Unknown"
        count = c.get("count") or c.get("product_count") or 0
        lines.append(f"- **{name}** ({count} products)")
    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))]), data


async def _handle_compare_products(args: dict[str, Any]) -> tuple[CallToolResult, dict | None]:
    product_ids = args.get("product_ids")
    if not product_ids or not isinstance(product_ids, list) or len(product_ids) < 2:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: At least 2 product_ids are required for comparison.")],
            isError=True,
        ), None
    try:
        data = await _api_get("/v1/products/compare", {"ids": ",".join(str(i) for i in product_ids)})
    except Exception as exc:
        logger.exception("compare_products API error for ids %r", product_ids)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Comparison failed: {exc}")],
            isError=True,
        ), None
    items = data.get("items", []) if isinstance(data, dict) else []
    if not items:
        return CallToolResult(
            content=[TextContent(type="text", text="No comparison results found.")]
        ), None
    lines = [f"Comparison of {len(items)} products:\n"]
    for i, p in enumerate(items, 1):
        lines.append(_fmt_product_summary(i, p))
    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))]), data


async def _api_get(path: str, params: dict[str, Any] | None = None) -> Any:
    import httpx
    from app.config import get_settings
    settings = get_settings()
    API_BASE_URL = settings.app_base_url or "http://localhost:8000"

    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient(base_url=API_BASE_URL, headers=headers, timeout=10.0) as client:
        resp = await client.get(path, params=params or {})
        resp.raise_for_status()
        return resp.json()


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


class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: dict[str, Any] | None = None
    id: Any = None


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Any
    result: Any | None = None
    error: dict[str, Any] | None = None


@router.post("/v1/tools/list")
async def list_tools(request: Request, api_key: ApiKey = Depends(get_current_api_key)):
    server = get_mcp_server()
    result = await server.list_tools()
    return JSONRPCResponse(id="pending", result=result)


@router.post("/v1/tools/call")
async def call_tool(
    request: Request,
    body: JSONRPCRequest,
    api_key: ApiKey = Depends(get_current_api_key),
):
    server = get_mcp_server()
    try:
        result = await server.call_tool(body.method, body.params or {})
        return JSONRPCResponse(id=body.id, result=result)
    except Exception as exc:
        logger.exception("MCP tool call error: %s %s", body.method, exc)
        return JSONRPCResponse(
            id=body.id,
            error={"code": -32603, "message": str(exc)}
        )