from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.affiliate_links import get_affiliate_url
from app.auth import get_current_api_key
from app.database import get_db
from app.models.product import ApiKey, Product
from app.rate_limit import limiter, rate_limit_from_request
from app.schemas.product import (
    ProductListResponse, ProductResponse, CompareResponse, CompareMatch,
    CompareMatrixRequest, CompareMatrixResponse, CompareMatrixEntry,
    TrendingResponse, TrendingMatch
)
from app import cache

router = APIRouter(prefix="/v1/products", tags=["products"])


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
        affiliate_url=get_affiliate_url(p.source, p.url) if p.url else None,
        image_url=p.image_url,
        category=p.category,
        category_path=p.category_path,
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
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> ProductListResponse:
    request.state.api_key = api_key

    cache_key = cache.build_cache_key(
        "products:search",
        q=q,
        category=category,
        min_price=str(min_price) if min_price is not None else None,
        max_price=str(max_price) if max_price is not None else None,
        source=source,
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
        ).order_by(
            text("ts_rank(title_search_vector, plainto_tsquery('english', :q_rank)) DESC").bindparams(q_rank=q)
        )
    else:
        base_query = base_query.order_by(Product.updated_at.desc())

    if category:
        base_query = base_query.where(Product.category.ilike(f"%{category}%"))
    if min_price is not None:
        base_query = base_query.where(Product.price >= min_price)
    if max_price is not None:
        base_query = base_query.where(Product.price <= max_price)
    if source:
        base_query = base_query.where(Product.source == source)

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
    )

    await cache.cache_set(cache_key, response.model_dump(mode="json"), ttl_seconds=600)

    return response


@router.get("/best-price", response_model=ProductResponse, summary="Find cheapest product across all platforms")
@limiter.limit(rate_limit_from_request)
async def best_price(
    request: Request,
    q: str = Query(..., min_length=1, description="Product name to search for"),
    category: Optional[str] = Query(None, description="Optional category filter"),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> ProductResponse:
    """Return the single cheapest listing for a product across all platforms."""
    request.state.api_key = api_key

    base_query = (
        select(Product)
        .where(Product.is_active == True)
        .where(
            text("title_search_vector @@ plainto_tsquery('english', :q)").bindparams(q=q)
        )
    )
    if category:
        base_query = base_query.where(Product.category.ilike(f"%{category}%"))

    base_query = base_query.order_by(Product.price.asc()).limit(1)
    result = await db.execute(base_query)
    product = result.scalar_one_or_none()

    if not product:
        # Fallback: ILIKE search for broader matching
        fallback = (
            select(Product)
            .where(Product.is_active == True)
            .where(Product.title.ilike(f"%{q}%"))
        )
        if category:
            fallback = fallback.where(Product.category.ilike(f"%{category}%"))
        fallback = fallback.order_by(Product.price.asc()).limit(1)
        result2 = await db.execute(fallback)
        product = result2.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No products found for: {q!r}")

    return _map_product(product)


@router.get("/compare", response_model=CompareResponse, summary="Compare same product across platforms")
@limiter.limit(rate_limit_from_request)
async def compare_product(
    request: Request,
    product_id: int = Query(..., description="Source product ID to find matches for"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price filter for matches"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price filter for matches"),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> CompareResponse:
    request.state.api_key = api_key

    cache_key = cache.build_cache_key(
        "products:compare",
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source product not found")

    from app.compare import ProductMatcher
    matcher = ProductMatcher(db)
    min_p = float(min_price) if min_price is not None else None
    max_p = float(max_price) if max_price is not None else None
    matches = await matcher.find_matches(source_product, min_p, max_p)

    match_responses = []
    for matched_product, score in matches:
        match_responses.append(CompareMatch(
            id=matched_product.id,
            sku=matched_product.sku,
            source=matched_product.source,
            merchant_id=matched_product.merchant_id,
            name=matched_product.title,
            description=matched_product.description,
            price=matched_product.price,
            currency=matched_product.currency,
            buy_url=matched_product.url,
            affiliate_url=get_affiliate_url(matched_product.source, matched_product.url) if matched_product.url else None,
            image_url=matched_product.image_url,
            category=matched_product.category,
            category_path=matched_product.category_path,
            availability=matched_product.is_active,
            metadata=matched_product.metadata_,
            updated_at=matched_product.updated_at,
            match_score=round(score, 3),
        ))

    match_responses.sort(key=lambda x: x.price)

    response = CompareResponse(
        source_product_id=source_product.id,
        source_product_name=source_product.title,
        matches=match_responses,
        total_matches=len(match_responses),
    )

    await cache.cache_set(cache_key, response.model_dump(mode="json"), ttl_seconds=300)

    return response


@router.post("/compare", response_model=CompareMatrixResponse, summary="Compare multiple products across platforms")
@limiter.limit(rate_limit_from_request)
async def compare_products_matrix(
    request: Request,
    body: CompareMatrixRequest,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> CompareMatrixResponse:
    request.state.api_key = api_key

    cache_key = cache.build_cache_key(
        "products:compare_matrix",
        product_ids=sorted(body.product_ids),
        min_price=str(body.min_price) if body.min_price is not None else None,
        max_price=str(body.max_price) if body.max_price is not None else None,
    )
    cached = await cache.cache_get(cache_key)
    if cached:
        return CompareMatrixResponse(**cached)

    from app.compare import ProductMatcher
    matcher = ProductMatcher(db)

    comparisons = []
    for product_id in body.product_ids:
        source_result = await db.execute(
            select(Product).where(Product.id == product_id, Product.is_active == True)
        )
        source_product = source_result.scalar_one_or_none()
        if not source_product:
            continue

        min_p = float(body.min_price) if body.min_price is not None else None
        max_p = float(body.max_price) if body.max_price is not None else None
        matches = await matcher.find_matches(source_product, min_p, max_p)

        match_responses = []
        for matched_product, score in matches:
            match_responses.append(CompareMatch(
                id=matched_product.id,
                sku=matched_product.sku,
                source=matched_product.source,
                merchant_id=matched_product.merchant_id,
                name=matched_product.title,
                description=matched_product.description,
                price=matched_product.price,
                currency=matched_product.currency,
                buy_url=matched_product.url,
                affiliate_url=get_affiliate_url(matched_product.source, matched_product.url) if matched_product.url else None,
                image_url=matched_product.image_url,
                category=matched_product.category,
                category_path=matched_product.category_path,
                availability=matched_product.is_active,
                metadata=matched_product.metadata_,
                updated_at=matched_product.updated_at,
                match_score=round(score, 3),
            ))

        match_responses.sort(key=lambda x: x.price)

        comparisons.append(CompareMatrixEntry(
            source_product_id=source_product.id,
            source_product_name=source_product.title,
            matches=match_responses,
            total_matches=len(match_responses),
        ))

    response = CompareMatrixResponse(
        comparisons=comparisons,
        total_products=len(comparisons),
    )

    await cache.cache_set(cache_key, response.model_dump(mode="json"), ttl_seconds=300)

    return response


@router.get("/trending", response_model=TrendingResponse, summary="Get trending products by category")
@limiter.limit(rate_limit_from_request)
async def get_trending_products(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category name"),
    limit: int = Query(50, ge=1, le=100, description="Number of products to return"),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> TrendingResponse:
    request.state.api_key = api_key

    cache_key = cache.build_cache_key(
        "products:trending",
        category=category,
        limit=limit,
    )
    cached = await cache.cache_get(cache_key)
    if cached:
        return TrendingResponse(**cached)

    base_query = (
        select(Product)
        .where(Product.is_active == True)
        .order_by(Product.updated_at.desc())
    )

    if category:
        base_query = base_query.where(Product.category.ilike(f"%{category}%"))

    results = await db.execute(base_query.limit(limit))
    products = results.scalars().all()

    items = []
    for p in products:
        items.append(TrendingMatch(
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
            category=p.category,
            category_path=p.category_path,
            availability=p.is_active,
            metadata=p.metadata_,
            updated_at=p.updated_at,
        ))

    response = TrendingResponse(
        category=category,
        items=items,
        total=len(items),
    )

    await cache.cache_set(cache_key, response.model_dump(mode="json"), ttl_seconds=300)

    return response


@router.get("/{product_id}", response_model=ProductResponse, summary="Get product by ID")
@limiter.limit(rate_limit_from_request)
async def get_product(
    request: Request,
    product_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> ProductResponse:
    request.state.api_key = api_key

    cache_key = f"products:item:{product_id}"
    cached = await cache.cache_get(cache_key)
    if cached:
        return ProductResponse(**cached)

    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.is_active == True)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    response = _map_product(product)
    await cache.cache_set(cache_key, response.model_dump(mode="json"), ttl_seconds=600)

    return response
