from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_api_key
from app.database import get_db
from app.models.product import ApiKey, Product
from app.rate_limit import limiter, rate_limit_from_request
from app.schemas.product import ProductListResponse, ProductResponse
from app.affiliate_links import get_affiliate_url
from app import cache

router = APIRouter(prefix="/v1/search", tags=["search"])


def _map_product(p: Product) -> ProductResponse:
    return ProductResponse(
        id=p.id,
        sku=p.sku,
        source=p.source,
        merchant_id=p.merchant_id,
        name=p.title,
        description=p.description,
        price=p.price,
        currency=p.currency,
        buy_url=p.url,
        affiliate_url=get_affiliate_url(p.source, p.url, p.id) if p.url else None,
        image_url=p.image_url,
        brand=p.brand,
        category=p.category,
        category_path=p.category_path,
        rating=p.rating,
        availability=p.is_active,
        metadata=p.metadata_,
        updated_at=p.updated_at,
    )


@router.get("", response_model=ProductListResponse, summary="Search products")
@limiter.limit(rate_limit_from_request)
async def search_products(
    request: Request,
    q: Optional[str] = Query(None, description="Full-text search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    platform: Optional[str] = Query(None, description="Filter by platform (source)"),
    in_stock: Optional[bool] = Query(None, description="Filter by availability"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> ProductListResponse:
    request.state.api_key = api_key

    cache_key = cache.build_cache_key(
        "search:query",
        q=q,
        category=category,
        min_price=str(min_price) if min_price is not None else None,
        max_price=str(max_price) if max_price is not None else None,
        platform=platform,
        in_stock=str(in_stock) if in_stock is not None else None,
        limit=limit,
        offset=offset,
    )

    cached = await cache.cache_get(cache_key)
    if cached:
        return ProductListResponse(**cached)

    base_query = select(Product).where(Product.is_active == True)

    if q:
        base_query = base_query.where(
            text("title_search_vector @@ plainto_tsquery('english', :q)").bindparams(q=q)
        )
        title_rank = text("ts_rank(title_search_vector, plainto_tsquery('english', :q_title)) DESC").bindparams(q_title=q)
        desc_rank = text("ts_rank(to_tsvector('english', coalesce(description, '')), plainto_tsquery('english', :q_desc)) DESC").bindparams(q_desc=q)
        base_query = base_query.order_by(
            title_rank,
            desc_rank,
            Product.updated_at.desc()
        )
    else:
        base_query = base_query.order_by(Product.updated_at.desc())

    if category:
        base_query = base_query.where(Product.category.ilike(f"%{category}%"))
    if min_price is not None:
        base_query = base_query.where(Product.price >= min_price)
    if max_price is not None:
        base_query = base_query.where(Product.price <= max_price)
    if platform is not None:
        base_query = base_query.where(Product.source == platform)
    if in_stock is not None:
        base_query = base_query.where(Product.is_active == in_stock)

    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    results = await db.execute(base_query.limit(limit).offset(offset))
    products = results.scalars().all()

    response = ProductListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[_map_product(p) for p in products],
        has_more=(offset + limit) < total,
    )

    await cache.cache_set(cache_key, response.model_dump(mode="json"), ttl_seconds=600)

    return response