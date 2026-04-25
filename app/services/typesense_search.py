"""Typesense-backed fast search for product catalog.

Returns product UUIDs from Typesense (8-25ms), which the caller then
hydrates from Postgres. Falls back gracefully when Typesense is unavailable
or returns no results.
"""
from __future__ import annotations

import os
from typing import Optional

import httpx

from app.logging_centralized import get_logger

logger = get_logger("typesense-search-service")

_TYPESENSE_URL = os.getenv("TYPESENSE_URL", "http://buywhere-typesense-1:8108")
_TYPESENSE_API_KEY = os.getenv("TYPESENSE_API_KEY", "")
_COLLECTION = "products"
_TIMEOUT = 5.0  # seconds — fast or fallback

# Shared async client (module-level singleton, thread-safe for asyncio)
_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=_TYPESENSE_URL,
            headers={"X-TYPESENSE-API-KEY": _TYPESENSE_API_KEY},
            timeout=_TIMEOUT,
        )
    return _client


async def typesense_search(
    q: str,
    *,
    category: Optional[str] = None,
    platform: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    limit: int = 20,
    offset: int = 0,
) -> Optional[tuple[list[str], int]]:
    """Search Typesense and return (product_ids, found_count).

    Returns None on any error so the caller can fall back to Postgres.
    """
    if not _TYPESENSE_API_KEY:
        return None

    params: dict = {
        "q": q,
        "query_by": "name,description,brand",
        "per_page": min(limit, 250),
        "page": (offset // limit) + 1 if limit > 0 else 1,
        "include_fields": "id",
    }

    filter_parts: list[str] = ["availability:=true"]
    if category:
        filter_parts.append(f"category_path:={category}")
    if platform:
        filter_parts.append(f"platform:={platform}")
    if price_min is not None:
        filter_parts.append(f"price:>={price_min}")
    if price_max is not None:
        filter_parts.append(f"price:<={price_max}")
    if filter_parts:
        params["filter_by"] = " && ".join(filter_parts)

    try:
        client = _get_client()
        resp = await client.get(
            f"/collections/{_COLLECTION}/documents/search",
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        ids = [hit["document"]["id"] for hit in data.get("hits", [])]
        found = data.get("found", len(ids))
        return ids, found
    except Exception as exc:
        logger.warning("Typesense search failed, falling back to Postgres: %s", exc)
        return None


async def typesense_autocomplete(
    q: str,
    *,
    limit: int = 10,
) -> Optional[tuple[list[str], int]]:
    """Fast prefix autocomplete from Typesense.

    Returns (suggestion_strings, found_count) on success, None on failure.
    Uses prefix query on product names for fast suggestion completion.
    """
    if not _TYPESENSE_API_KEY:
        return None

    params: dict = {
        "q": q,
        "query_by": "name",
        "prefix_search": "true",
        "per_page": limit,
        "include_fields": "name",
    }

    try:
        client = _get_client()
        resp = await client.get(
            f"/collections/{_COLLECTION}/documents/search",
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        names = [hit["document"]["name"] for hit in data.get("hits", [])]
        found = data.get("found", len(names))
        deduped = list(dict.fromkeys(names))
        return deduped, found
    except Exception as exc:
        logger.warning("Typesense autocomplete failed, falling back to Postgres: %s", exc)
        return None
