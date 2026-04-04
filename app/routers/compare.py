import logging
from typing import Optional, List
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_api_key
from app.database import get_db
from app.models.product import ApiKey, Product
from app.rate_limit import limiter, rate_limit_from_request
from app.schemas.product import (
    CompareResponse,
    CompareMatch,
    CompareHighlights,
)
from app import cache
from app.affiliate_links import get_affiliate_url
from app.compare import ProductMatcher

logger = logging.getLogger("buywhere_api")

router = APIRouter(prefix="/v1/compare", tags=["compare"])


def _build_compare_match(p: Product, score: float) -> CompareMatch:
    return CompareMatch(
        id=p.id,
        sku=p.sku,
        source=p.source,
        merchant_id=p.merchant_id,
        name=p.title,
        description=p.description,
        price=p.price,
        currency=p.currency,
        buy_url=p.url,
        affiliate_url=get_affiliate_url(p.source, p.url) if p.url else None,
        image_url=p.image_url,
        brand=p.brand,
        category=p.category,
        category_path=p.category_path,
        rating=p.rating,
        is_available=p.is_available,
        last_checked=p.last_checked,
        metadata=p.metadata_,
        updated_at=p.updated_at,
        match_score=round(score, 3),
    )


def _get_highlights(matches: List[CompareMatch]) -> Optional[CompareHighlights]:
    if not matches:
        return None

    cheapest = min(matches, key=lambda x: x.price, default=None)
    best_rated = max((m for m in matches if m.rating is not None), key=lambda x: x.rating, default=None)

    fastest_shipping = None
    fastest_shipping_days = None
    for m in matches:
        if m.metadata and isinstance(m.metadata, dict):
            shipping = m.metadata.get("shipping_days") or m.metadata.get("shipping")
            if shipping is not None:
                try:
                    shipping_int = int(shipping)
                    if fastest_shipping_days is None or shipping_int < fastest_shipping_days:
                        fastest_shipping_days = shipping_int
                        fastest_shipping = m
                except (ValueError, TypeError):
                    pass

    if not cheapest and not best_rated and not fastest_shipping:
        return None

    return CompareHighlights(
        cheapest=cheapest,
        best_rated=best_rated,
        fastest_shipping=fastest_shipping,
    )


@router.get("/{product_id}", response_model=CompareResponse, summary="Compare same product across all sources")
@limiter.limit(rate_limit_from_request)
async def compare_product_by_id(
    request: Request,
    product_id: int,
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> CompareResponse:
    """Find the same product across all sources using title similarity + brand match.
    
    Returns products sorted by price with savings vs most expensive.
    This is THE killer feature for shopping agents.
    """
    request.state.api_key = api_key

    cache_key = cache.build_cache_key(
        "compare:product",
        product_id=product_id,
        min_price=str(min_price) if min_price is not None else None,
        max_price=str(max_price) if max_price is not None else None,
    )
    cached = await cache.cache_get(cache_key)
    if cached:
        return CompareResponse(**cached)

    source_result = await db.execute(
        select(Product).where(Product.id == product_id, Product.is_active == True)
    )
    source_product = source_result.scalar_one_or_none()
    if not source_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    matcher = ProductMatcher(db)
    matches_with_scores = await matcher.find_matches(source_product, min_price, max_price)

    matches: List[CompareMatch] = []
    for matched_product, score in matches_with_scores:
        matches.append(_build_compare_match(matched_product, score))

    matches.sort(key=lambda x: x.price)

    most_expensive_price = max((m.price for m in matches), default=None)
    if most_expensive_price and most_expensive_price > 0:
        for m in matches:
            savings = most_expensive_price - m.price
            savings_pct = (savings / most_expensive_price) * 100
            m.savings_vs_most_expensive = float(savings)
            m.savings_pct = round(float(savings_pct), 2)

    highlights = _get_highlights(matches) if matches else None

    response = CompareResponse(
        source_product_id=source_product.id,
        source_product_name=source_product.title,
        matches=matches,
        total_matches=len(matches),
        highlights=highlights,
    )

    await cache.cache_set(cache_key, response.model_dump(mode="json"), ttl_seconds=300)

    return response