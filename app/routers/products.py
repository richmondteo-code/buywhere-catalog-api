import csv
import io
import json
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
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
    TrendingResponse, TrendingMatch,
    CompareDiffRequest, CompareDiffResponse, CompareDiffEntry, FieldDiff,
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
        brand=p.brand,
        category=p.category,
        category_path=p.category_path,
        rating=p.rating,
        is_available=p.is_available,
        last_checked=p.last_checked,
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

    cache_key = cache.build_cache_key(
        "products:best_price",
        q=q,
        category=category,
    )
    cached = await cache.cache_get(cache_key)
    if cached:
        return ProductResponse(**cached)

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

    response = _map_product(product)
    await cache.cache_set(cache_key, response.model_dump(mode="json"), ttl_seconds=300)
    return response


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
            brand=matched_product.brand,
            category=matched_product.category,
            category_path=matched_product.category_path,
            rating=matched_product.rating,
            is_available=matched_product.is_available,
            last_checked=matched_product.last_checked,
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
                brand=matched_product.brand,
                category=matched_product.category,
                category_path=matched_product.category_path,
                rating=matched_product.rating,
                is_available=matched_product.is_available,
                last_checked=matched_product.last_checked,
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


@router.post("/compare/diff", response_model=CompareDiffResponse, summary="Compare 2-5 products directly — returns structured diff")
@limiter.limit(rate_limit_from_request)
async def compare_products_diff(
    request: Request,
    body: CompareDiffRequest,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> CompareDiffResponse:
    request.state.api_key = api_key

    cache_key = cache.build_cache_key(
        "products:compare_diff",
        product_ids=sorted(body.product_ids),
        include_image=body.include_image_similarity,
    )
    cached = await cache.cache_get(cache_key)
    if cached:
        return CompareDiffResponse(**cached)

    if len(body.product_ids) < 2 or len(body.product_ids) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="product_ids must contain between 2 and 5 IDs",
        )

    result = await db.execute(
        select(Product).where(
            Product.id.in_(body.product_ids),
            Product.is_active == True,
        )
    )
    products = result.scalars().all()

    if len(products) != len(body.product_ids):
        found_ids = {p.id for p in products}
        missing = [id for id in body.product_ids if id not in found_ids]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Products not found: {missing}",
        )

    sorted_products = sorted(products, key=lambda p: p.price)
    price_ranks = {p.id: i + 1 for i, p in enumerate(sorted_products)}

    entries = []
    for p in products:
        entries.append(CompareDiffEntry(
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
            price_rank=price_ranks[p.id],
        ))

    compared_fields = [
        ("price", lambda p: p.price),
        ("currency", lambda p: p.currency),
        ("brand", lambda p: p.brand),
        ("category", lambda p: p.category),
        ("source", lambda p: p.source),
        ("availability", lambda p: p.is_available),
    ]

    field_diffs = []
    identical_fields = []

    for field_name, accessor in compared_fields:
        values = [accessor(p) for p in products]
        all_identical = len(set(str(v) for v in values)) <= 1
        if all_identical:
            identical_fields.append(field_name)
        else:
            field_diffs.append(FieldDiff(
                field=field_name,
                values=values,
                all_identical=False,
            ))

    cheapest = sorted_products[0]
    most_expensive = sorted_products[-1]
    spread = most_expensive.price - cheapest.price
    spread_pct = float(spread / cheapest.price * 100) if cheapest.price > 0 else 0.0

    response = CompareDiffResponse(
        products=entries,
        field_diffs=field_diffs,
        identical_fields=identical_fields,
        cheapest_product_id=cheapest.id,
        most_expensive_product_id=most_expensive.id,
        price_spread=spread,
        price_spread_pct=round(spread_pct, 2),
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
            brand=p.brand,
            category=p.category,
            category_path=p.category_path,
            rating=p.rating,
            is_available=p.is_available,
            last_checked=p.last_checked,
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


@router.get("/export", summary="Export products as CSV or JSON")
@limiter.limit(rate_limit_from_request)
async def export_products(
    request: Request,
    format: str = Query("json", regex="^(csv|json)$", description="Export format: csv or json"),
    category: Optional[str] = Query(None, description="Filter by category"),
    source: Optional[str] = Query(None, description="Filter by source/platform"),
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    limit: int = Query(1000, ge=1, le=10000, description="Max records to export (up to 10K)"),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> StreamingResponse:
    request.state.api_key = api_key

    base_query = select(Product).where(Product.is_active == True)

    if category:
        base_query = base_query.where(Product.category.ilike(f"%{category}%"))
    if source:
        base_query = base_query.where(Product.source == source)
    if min_price is not None:
        base_query = base_query.where(Product.price >= min_price)
    if max_price is not None:
        base_query = base_query.where(Product.price <= max_price)

    base_query = base_query.order_by(Product.id).limit(limit).offset(offset)

    results = await db.execute(base_query)
    products = results.scalars().all()

    if format == "csv":
        async def csv_stream():
            output = io.StringIO()
            fieldnames = [
                "id", "sku", "source", "merchant_id", "title", "description",
                "price", "currency", "url", "brand", "category", "image_url",
                "is_active", "rating", "updated_at"
            ]
            await output.write(",".join(fieldnames) + "\n")

            for p in products:
                row = {
                    "id": p.id,
                    "sku": p.sku or "",
                    "source": p.source or "",
                    "merchant_id": p.merchant_id or "",
                    "title": (p.title or "").replace('"', '""'),
                    "description": (p.description or "").replace("\n", " ").replace("\r", "").replace('"', '""'),
                    "price": str(p.price) if p.price else "",
                    "currency": p.currency or "SGD",
                    "url": p.url or "",
                    "brand": p.brand or "",
                    "category": p.category or "",
                    "image_url": p.image_url or "",
                    "is_active": str(p.is_active) if p.is_active is not None else "",
                    "rating": str(p.rating) if p.rating else "",
                    "updated_at": p.updated_at.isoformat() if p.updated_at else "",
                }
                await output.write(",".join(f'"{v}"' if '"' in str(v) or ',' in str(v) else str(v) for v in row.values()) + "\n")
                if output.tell() > 65536:
                    yield output.getvalue().encode("utf-8")
                    output.truncate(0)
                    output.seek(0)
            yield output.getvalue().encode("utf-8")

        return StreamingResponse(
            csv_stream(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=products_export_{offset}-{offset + len(products)}.csv"
            }
        )
    else:
        async def json_stream():
            buffer = io.BytesIO()
            await buffer.write(b"[")
            first = True
            for p in products:
                if not first:
                    await buffer.write(b",")
                first = False
                obj = {
                    "id": p.id,
                    "sku": p.sku,
                    "source": p.source,
                    "merchant_id": p.merchant_id,
                    "name": p.title,
                    "description": p.description,
                    "price": str(p.price) if p.price else None,
                    "currency": p.currency or "SGD",
                    "buy_url": p.url,
                    "brand": p.brand,
                    "category": p.category,
                    "category_path": p.category_path,
                    "image_url": p.image_url,
                    "availability": p.is_active,
                    "rating": str(p.rating) if p.rating else None,
                    "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                }
                await buffer.write(json.dumps(obj, ensure_ascii=False).encode("utf-8"))
                if buffer.tell() > 65536:
                    yield buffer.getvalue()
                    buffer.truncate(0)
                    buffer.seek(0)
            await buffer.write(b"]")
            yield buffer.getvalue()

        return StreamingResponse(
            json_stream(),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=products_export_{offset}-{offset + len(products)}.json"
            }
        )


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
