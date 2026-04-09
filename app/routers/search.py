import logging
import time
from decimal import Decimal
from typing import Optional, List, Tuple
from urllib.parse import urlparse

import httpx
import imagehash
from PIL import Image
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import StringConstraints, BaseModel, Field
from sqlalchemy import func, select, text
import typing
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_api_key
from app.database import get_db
from app.models.product import ApiKey, Product, ImageHash
from app.models.search_history import SearchHistory
from app.rate_limit import limiter, rate_limit_from_request
from app.schemas.product import ProductListResponse, ProductResponse, SearchSuggestionResponse, SearchSuggestion, AutocompleteResponse, AutocompleteSuggestion, FacetBucket, PriceFacetBucket, RatingFacetBucket, SearchFiltersResponse
from app.schemas.search_history import SearchHistoryListResponse, SearchHistoryEntry
from app.affiliate_links import get_affiliate_url
from app.services.currency import SUPPORTED_CURRENCIES, convert_price, get_rate_for_header
from app import cache
from app.routers.search_i18n import translate_query
from app.services.semantic_search import semantic_search_service

SUPPORTED_SEARCH_LANGS = ("ms", "th", "vi", "id", "en")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])

SOURCE_TO_COUNTRY = {
    "shopee_sg": "SG",
    "lazada_sg": "SG",
    "carousell_sg": "SG",
    "qoo10_sg": "SG",
    "shopee_my": "MY",
    "lazada_my": "MY",
    "shopee_ph": "PH",
    "lazada_ph": "PH",
    "shopee_th": "TH",
    "lazada_th": "TH",
    "shopee_vn": "VN",
    "lazada_vn": "VN",
}

COUNTRY_NAMES = {
    "SG": "Singapore",
    "MY": "Malaysia",
    "PH": "Philippines",
    "TH": "Thailand",
    "VN": "Vietnam",
}

BENCHMARK_QUERIES = [
    "nike shoes",
    "iphone 15 case",
    "samsung tv 55 inch",
    "adidas shorts",
    "wireless earbuds",
    "laptop stand",
    "coffee maker",
    "running shoes men",
    "bluetooth speaker",
    "desk lamp",
]


def _map_product(p: Product, target_currency: Optional[str] = None, confidence_score: Optional[float] = None) -> ProductResponse:
    price = float(p.price) if p.price is not None else 0.0
    currency = str(p.currency) if p.currency is not None else "SGD"
    if target_currency and target_currency != currency:
        converted = convert_price(Decimal(str(price)), currency, target_currency)
        if converted is not None:
            price = float(converted)
            currency = target_currency
    return ProductResponse(
        id=int(p.id) if p.id is not None else 0,
        sku=str(p.sku) if p.sku is not None else "",
        source=str(p.source) if p.source is not None else "",
        merchant_id=str(p.merchant_id) if p.merchant_id is not None else "",
        name=str(p.title) if p.title is not None else "",
        description=str(p.description) if p.description is not None else None,
        price=Decimal(str(price)),
        currency=currency,
        price_sgd=Decimal(str(p.price_sgd)) if p.price_sgd is not None else None,
        converted_price=Decimal(str(converted)) if target_currency and target_currency != currency and 'converted' in locals() else None,
        converted_currency=target_currency if target_currency and target_currency != currency else None,
        buy_url=str(p.url) if p.url is not None else "",
        affiliate_url=get_affiliate_url(str(p.source) if p.source else "", str(p.url) if p.url else "", int(p.id) if p.id else 0) if p.url else None,
        image_url=str(p.image_url) if p.image_url is not None else None,
        barcode=str(p.barcode) if p.barcode is not None else None,
        brand=str(p.brand) if p.brand is not None else None,
        category=str(p.category) if p.category is not None else None,
        category_path=list(p.category_path) if p.category_path is not None else None,
        rating=Decimal(str(p.rating)) if p.rating is not None else None,
        review_count=int(p.review_count) if p.review_count is not None else None,
        avg_rating=Decimal(str(p.avg_rating)) if p.avg_rating is not None else None,
        rating_source=str(p.rating_source) if p.rating_source is not None else None,
        is_available=bool(p.is_active) if p.is_active is not None else False,
        in_stock=bool(p.in_stock) if p.in_stock is not None else None,
        stock_level=str(p.stock_level) if p.stock_level is not None else None,
        last_checked=p.last_checked,
        data_updated_at=p.data_updated_at,
        availability_prediction=None,  # Would need to be computed from historical stock patterns
        competitor_count=None,  # Would need to be computed by counting matching products across sources
        metadata=p.metadata_,
        updated_at=p.updated_at,
        price_trend=None,  # Would need to be computed from price history
        confidence_score=confidence_score,
    )


@router.get("", response_model=ProductListResponse, summary="Search products")
@limiter.limit(rate_limit_from_request)
async def search_products(
    request: Request,
    q: Optional[str] = Query(None, max_length=500, description="Full-text search query (max 500 chars)"),
    lang: Optional[str] = Query(None, description="Query language for translation: ms (Malay), th (Thai), vi (Vietnamese), id (Indonesian). Translated to English for matching."),
    category: Optional[str] = Query(None, max_length=200, description="Filter by category"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price filter"),
    platform: Optional[str] = Query(None, max_length=100, description="Filter by platform (source)"),
    country: Optional[str] = Query(None, description="Filter by country code(s), comma-separated (e.g., SG,MY)"),
    in_stock: Optional[bool] = Query(None, description="Filter by availability"),
    currency: Optional[str] = Query(None, description=f"Target currency for price conversion. Supported: {', '.join(SUPPORTED_CURRENCIES)}"),
    limit: int = Query(20, ge=1, le=100, description="Results per page (1-100)"),
    offset: int = Query(0, ge=0, le=10000, description="Pagination offset (0-10000)"),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> ProductListResponse:
    request.state.api_key = api_key

    if q and len(q) > 500:
        suggested_query = q[:500]
        raise HTTPException(
            status_code=422,
            detail={
                "code": "QUERY_TOO_LONG",
                "field": "q",
                "message": f"Query exceeds maximum length of 500 characters (got {len(q)})",
                "max_length": 500,
                "actual_length": len(q),
                "suggested_query": suggested_query,
            }
        )

    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_PRICE_RANGE",
                "field": "min_price,max_price",
                "message": "min_price cannot be greater than max_price",
                "min_price": str(min_price),
                "max_price": str(max_price),
            }
        )

    if currency is not None and currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "UNSUPPORTED_CURRENCY",
                "field": "currency",
                "message": f"Unsupported currency: {currency}. Supported: {', '.join(SUPPORTED_CURRENCIES)}",
                "provided": currency,
                "supported": list(SUPPORTED_CURRENCIES),
            }
        )

    if lang is not None and lang.lower() not in SUPPORTED_SEARCH_LANGS:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "UNSUPPORTED_LANGUAGE",
                "field": "lang",
                "message": f"Unsupported lang: {lang}. Supported: {', '.join(SUPPORTED_SEARCH_LANGS)}",
                "provided": lang,
                "supported": list(SUPPORTED_SEARCH_LANGS),
            }
        )

    if lang and q:
        q = translate_query(q, lang)

    if country is not None:
        country_codes = [c.strip().upper() for c in country.split(",")]
        invalid = [c for c in country_codes if c not in COUNTRY_NAMES]
        if invalid:
            raise HTTPException(status_code=422, detail=f"Invalid country code(s): {', '.join(invalid)}. Supported: {', '.join(COUNTRY_NAMES.keys())}")

    default_currency = "SGD"
    cache_key = cache.build_cache_key(
        "search:query",
        q=q,
        lang=lang,
        category=category,
        min_price=str(min_price) if min_price is not None else None,
        max_price=str(max_price) if max_price is not None else None,
        platform=platform,
        country=country,
        in_stock=str(in_stock) if in_stock is not None else None,
        currency=currency,
        limit=limit,
        offset=offset,
    )

    cached = await cache.cache_get(cache_key)
    if cached:
        response = ProductListResponse.model_construct(**cached)
        if currency and currency != default_currency:
            rate_header = get_rate_for_header(default_currency, currency)
            if rate_header:
                request.state.response_headers = {"X-Currency-Rate": f"{default_currency}->{currency}:{rate_header}"}
        return response

    start_time = time.perf_counter()

    base_query = select(Product).where(Product.is_active == True)

    if q:
        base_query = base_query.where(
            text("search_vector @@ websearch_to_tsquery('english', :q)").bindparams(q=q)
        )
        bm25_rank = text(
            "ts_rank_cd(search_vector, websearch_to_tsquery('english', :q_rank), 32)"
        ).bindparams(q_rank=q)
        base_query = base_query.add_columns(
            bm25_rank.label("rank")
        ).order_by(
            text("ts_rank_cd(search_vector, websearch_to_tsquery('english', :q_rank), 32) DESC").bindparams(q_rank=q),
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
    if country is not None:
        country_codes = [c.strip().upper() for c in country.split(",")]
        source_countries = [(src, cc) for src, cc in SOURCE_TO_COUNTRY.items() if cc in country_codes]
        if source_countries:
            source_conditions = [Product.source == src for src, _ in source_countries]
            from sqlalchemy import or_
            base_query = base_query.where(or_(*source_conditions))

    if offset == 0:
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()
    else:
        total = None

    results = await db.execute(base_query.limit(limit).offset(offset))
    if q:
        # When q is provided, we have rank column in results
        product_data = []
        for row in results:
            product = row.Product  # Access the Product object from the tuple
            rank = row.rank if hasattr(row, 'rank') else 0.0
            # Normalize rank to 0-1 confidence score (ts_rank_cd returns 0-1 typically)
            confidence_score = min(max(float(rank), 0.0), 1.0)
            product_data.append((product, confidence_score))
        products = [p for p, _ in product_data]
        confidences = [c for _, c in product_data]
    else:
        products = results.scalars().all()
        confidences = [None] * len(products)

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    if q:
        logger.info(
            "Search query=%r category=%r platform=%r elapsed_ms=%.2f total=%d",
            q, category, platform, elapsed_ms, total
        )

    target_currency = currency if currency else default_currency
    if q:
        items = [_map_product(p, target_currency, confidence) for p, confidence in zip(products, confidences)]
    else:
        items = [_map_product(p, target_currency) for p in products]
    has_more = len(items) == limit if total is None else (offset + limit) < total
    effective_total = total if total is not None else offset + len(items)

    response_data = {
        "total": effective_total,
        "limit": limit,
        "offset": offset,
        "items": items,
        "has_more": has_more,
    }

    await cache.cache_set(cache_key, response_data, ttl_seconds=cache.TTL_SEARCH)

    if target_currency != default_currency:
        rate_header = get_rate_for_header(default_currency, target_currency)
        if rate_header:
            request.state.response_headers = {"X-Currency-Rate": f"{default_currency}->{target_currency}:{rate_header}"}

    search_history_entry = SearchHistory(
        developer_id=api_key.developer_id,
        api_key_id=api_key.id,
        query=q,
        filters={
            "category": category,
            "min_price": str(min_price) if min_price is not None else None,
            "max_price": str(max_price) if max_price is not None else None,
            "platform": platform,
            "country": country,
            "in_stock": in_stock,
        },
        result_count=effective_total,
    )
    db.add(search_history_entry)
    await db.flush()

    return ProductListResponse.model_construct(**response_data)


@router.get("/semantic", response_model=ProductListResponse, summary="Semantic search products")
@limiter.limit(rate_limit_from_request)
async def semantic_search_products(
    request: Request,
    q: str = Query(..., min_length=1, description="Semantic search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    platform: Optional[str] = Query(None, description="Filter by platform (source)"),
    currency: Optional[str] = Query(
        None,
        description=f"Target currency for price conversion. Supported: {', '.join(SUPPORTED_CURRENCIES)}",
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=10000),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> ProductListResponse:
    request.state.api_key = api_key

    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=422, detail="min_price cannot be greater than max_price")

    if currency is not None and currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported currency: {currency}. Supported: {', '.join(SUPPORTED_CURRENCIES)}",
        )

    cache_key = cache.build_cache_key(
        "search:semantic",
        q=q,
        category=category,
        min_price=str(min_price) if min_price is not None else None,
        max_price=str(max_price) if max_price is not None else None,
        platform=platform,
        currency=currency,
        limit=limit,
        offset=offset,
    )
    cached = await cache.cache_get(cache_key)
    if cached:
        response = ProductListResponse(**cached)
        if currency and currency != "SGD":
            rate_header = get_rate_for_header("SGD", currency)
            if rate_header:
                request.state.response_headers = {
                    "X-Currency-Rate": f"SGD->{currency}:{rate_header}"
                }
        return response

    result = await semantic_search_service.search(
        db,
        q=q,
        category=category,
        min_price=min_price,
        max_price=max_price,
        platform=platform,
        limit=limit,
        offset=offset,
    )

    target_currency = currency or "SGD"
    response = ProductListResponse(
        total=result.total,
        limit=limit,
        offset=offset,
        items=[_map_product(product, target_currency) for product in result.products],
        has_more=(offset + limit) < result.total,
    )

    await cache.cache_set(cache_key, response.model_dump(mode="json"), ttl_seconds=600)

    if target_currency != "SGD":
        rate_header = get_rate_for_header("SGD", target_currency)
        if rate_header:
            request.state.response_headers = {
                "X-Currency-Rate": f"SGD->{target_currency}:{rate_header}"
            }

    if result.fallback_used:
        request.state.response_headers = {
            **getattr(request.state, "response_headers", {}),
            "X-Semantic-Search": "fallback",
        }
    else:
        request.state.response_headers = {
            **getattr(request.state, "response_headers", {}),
            "X-Semantic-Search": "embeddings",
        }

    return response


@router.get("/suggest", response_model=AutocompleteResponse, summary="Search autocomplete with FTS prefix queries")
@limiter.limit(rate_limit_from_request)
async def search_suggestions(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query prefix"),
    limit: int = Query(10, ge=1, le=20, description="Max suggestions to return"),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> AutocompleteResponse:
    request.state.api_key = api_key

    cache_key = cache.build_cache_key(
        "search:autocomplete",
        q=q.lower(),
        limit=limit,
    )

    cached = await cache.cache_get(cache_key)
    if cached:
        return AutocompleteResponse(**cached)

    start_time = time.perf_counter()

    prefix = q.lower()

    fts_query = text("title_search_vector @@ to_tsquery('english', :prefix_q || ':*')").bindparams(prefix_q=prefix)

    title_query = (
        select(Product.title, func.count(Product.id).label("product_count"))
        .where(Product.is_active == True)
        .where(fts_query)
        .group_by(Product.title)
        .order_by(func.count(Product.id).desc())
        .limit(limit)
    )

    title_result = await db.execute(title_query)
    suggestions = [
        AutocompleteSuggestion(suggestion=row[0], product_count=row[1])
        for row in title_result.fetchall()
    ]

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "Autocomplete query=%r elapsed_ms=%.2f suggestions=%d",
        q, elapsed_ms, len(suggestions)
    )

    response = AutocompleteResponse(
        query=prefix,
        suggestions=suggestions,
        total=len(suggestions),
    )

    await cache.cache_set(cache_key, response.model_dump(mode="json"), ttl_seconds=300)

    return response


@router.get("/benchmark", summary="Benchmark search performance")
@limiter.limit(rate_limit_from_request)
async def benchmark_search(
    request: Request,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> dict:
    request.state.api_key = api_key

    results = []
    for q in BENCHMARK_QUERIES:
        start_time = time.perf_counter()

        base_query = (
            select(Product)
            .where(Product.is_active == True)
            .where(text("search_vector @@ websearch_to_tsquery('english', :q)").bindparams(q=q))
            .order_by(
                text(
                    "ts_rank_cd(search_vector, websearch_to_tsquery('english', :q_rank), 32) DESC"
                ).bindparams(q_rank=q)
            )
            .limit(20)
        )

        result = await db.execute(base_query)
        products = result.scalars().all()

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        results.append({
            "query": q,
            "elapsed_ms": round(elapsed_ms, 2),
            "result_count": len(products),
        })

    avg_ms = sum(r["elapsed_ms"] for r in results) / len(results) if results else 0
    return {
        "benchmarks": results,
        "average_ms": round(avg_ms, 2),
        "total_queries": len(results),
    }


SIMILARITY_THRESHOLD = 0.85
MAX_IMAGE_SEARCH_RESULTS = 20


class ImageSearchRequest(BaseModel):
    image_url: str = Field(..., description="URL of the image to search with")
    min_similarity: float = Field(0.8, ge=0.0, le=1.0, description="Minimum similarity score (0-1)")
    limit: int = Field(20, ge=1, le=50, description="Maximum number of results")


class ImageSearchMatch(BaseModel):
    id: int
    sku: str
    source: str
    merchant_id: str
    name: str
    description: Optional[str] = None
    price: Decimal
    currency: str
    buy_url: str
    affiliate_url: Optional[str] = None
    image_url: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    similarity_score: float
    model_config = {"from_attributes": True}


class ImageSearchResponse(BaseModel):
    query_image_url: str
    total_matches: int
    matches: List[ImageSearchMatch]


async def _fetch_image_and_hash(image_url: str, timeout: float = 5.0) -> Optional[str]:
    try:
        parsed = urlparse(image_url)
        if not parsed.scheme or not parsed.netloc:
            return None
    except Exception:
        return None

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(image_url)
            if response.status_code != 200:
                return None
            img = Image.open(BytesIO(response.content))
            img = img.convert("RGB")
            img = img.resize((256, 256))
            return str(imagehash.phash(img))
    except Exception:
        return None


def _compute_similarity(hash1: str, hash2: str) -> float:
    try:
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        return 1 - (h1 - h2) / (len(hash1) * 4)
    except Exception:
        return 0.0


@router.post("/image", response_model=ImageSearchResponse, summary="Find products by image similarity")
@limiter.limit(rate_limit_from_request)
async def search_by_image(
    request: Request,
    body: ImageSearchRequest,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> ImageSearchResponse:
    """Find products visually similar to the provided image.
    
    Uses perceptual hashing (pHash) to compare images. Returns products
    sorted by similarity score. Requires images to be indexed in the
    ImageHash table.
    """
    request.state.api_key = api_key

    query_hash = await _fetch_image_and_hash(body.image_url)
    if not query_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not fetch or hash the provided image URL"
        )

    result = await db.execute(select(ImageHash))
    all_hashes = result.scalars().all()

    similarities: List[Tuple[str, float]] = []
    for img_hash in all_hashes:
        sim = _compute_similarity(query_hash, img_hash.hash)
        if sim >= body.min_similarity:
            similarities.append((img_hash.original_url, sim))

    similarities.sort(key=lambda x: x[1], reverse=True)
    similarities = similarities[:body.limit]

    if not similarities:
        return ImageSearchResponse(
            query_image_url=body.image_url,
            total_matches=0,
            matches=[],
        )

    url_to_sim = {url: sim for url, sim in similarities}

    product_result = await db.execute(
        select(Product)
        .where(Product.is_active == True)
        .where(Product.image_url.in_(list(url_to_sim.keys())))
    )
    products = product_result.scalars().all()

    matches = []
    for product in products:
        sim = url_to_sim.get(product.image_url, 0.0)
        if sim >= body.min_similarity:
            matches.append(ImageSearchMatch(
                id=product.id,
                sku=product.sku,
                source=product.source,
                merchant_id=product.merchant_id,
                name=product.title,
                description=product.description,
                price=product.price,
                currency=product.currency,
                buy_url=product.url,
                affiliate_url=get_affiliate_url(product.source, product.url) if product.url else None,
                image_url=product.image_url,
                brand=product.brand,
                category=product.category,
                similarity_score=round(sim, 3),
            ))

    matches.sort(key=lambda x: x.similarity_score, reverse=True)

    return ImageSearchResponse(
        query_image_url=body.image_url,
        total_matches=len(matches),
        matches=matches,
    )


@router.get("/filters", response_model=SearchFiltersResponse, summary="Get available filter options with counts for building dynamic filter UIs")
@limiter.limit(rate_limit_from_request)
async def get_search_filters(
    request: Request,
    q: Optional[str] = Query(None, description="Optional search query to get filters scoped to results"),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
):
    request.state.api_key = api_key

    cache_key = cache.build_cache_key(
        "search:filters",
        q=q,
    )
    cached = await cache.cache_get(cache_key)
    if cached:
        return cached

    base_query = select(Product).where(Product.is_active == True)

    if q:
        base_query = base_query.where(
            text("search_vector @@ websearch_to_tsquery('english', :q)").bindparams(q=q)
        )

    category_query = (
        select(Product.category, func.count(Product.id))
        .where(Product.is_active == True)
        .where(Product.category.isnot(None), Product.category != "")
        .group_by(Product.category)
        .order_by(func.count(Product.id).desc())
        .limit(50)
    )
    if q:
        category_query = category_query.where(
            text("search_vector @@ websearch_to_tsquery('english', :q_cat)").bindparams(q_cat=q)
        )
    cat_result = await db.execute(category_query)
    categories = [FacetBucket(value=row[0], count=row[1]) for row in cat_result.all() if row[0]]

    brand_query = (
        select(Product.brand, func.count(Product.id))
        .where(Product.is_active == True)
        .where(Product.brand.isnot(None), Product.brand != "")
        .group_by(Product.brand)
        .order_by(func.count(Product.id).desc())
        .limit(50)
    )
    if q:
        brand_query = brand_query.where(
            text("search_vector @@ websearch_to_tsquery('english', :q_brand)").bindparams(q_brand=q)
        )
    brand_result = await db.execute(brand_query)
    brands = [FacetBucket(value=row[0], count=row[1]) for row in brand_result.all() if row[0]]

    platform_query = (
        select(Product.source, func.count(Product.id))
        .where(Product.is_active == True)
        .group_by(Product.source)
        .order_by(func.count(Product.id).desc())
    )
    if q:
        platform_query = platform_query.where(
            text("search_vector @@ websearch_to_tsquery('english', :q_plat)").bindparams(q_plat=q)
        )
    platform_result = await db.execute(platform_query)
    platforms = [FacetBucket(value=row[0], count=row[1]) for row in platform_result.all()]

    price_result = await db.execute(
        select(
            func.min(Product.price),
            func.max(Product.price),
        ).where(Product.is_active == True)
    )
    price_row = price_result.one()
    price_min = float(price_row[0] or 0)
    price_max = float(price_row[1] or 1000)

    price_ranges = []
    if price_max > price_min:
        bucket_size = 10 ** (len(str(int(price_max))) - 1)
        if bucket_size < 1:
            bucket_size = 1
        current = float(int(price_min / bucket_size) * bucket_size)
        while current < price_max:
            next_bucket = current + bucket_size
            bucket_count_result = await db.execute(
                select(func.count(Product.id))
                .where(Product.is_active == True)
                .where(Product.price >= current, Product.price < next_bucket)
            )
            count = bucket_count_result.scalar_one() or 0
            if count > 0:
                price_ranges.append(PriceFacetBucket(
                    min_price=Decimal(str(current)),
                    max_price=Decimal(str(next_bucket)) if next_bucket <= price_max else None,
                    count=count,
                ))
            current = next_bucket

    country_result = await db.execute(
        select(Product.source, func.count(Product.id))
        .where(Product.is_active == True)
        .group_by(Product.source)
    )
    country_counts: dict[str, int] = {code: 0 for code in COUNTRY_NAMES}
    for source, count in country_result.all():
        country_code = SOURCE_TO_COUNTRY.get(source)
        if country_code:
            country_counts[country_code] = country_counts.get(country_code, 0) + count
    countries = [
        FacetBucket(value=code, count=count)
        for code, count in country_counts.items()
        if count > 0
    ]
    countries.sort(key=lambda x: x.count, reverse=True)

    rating_ranges = []
    for min_r, max_r in [(4.0, 5.0), (3.0, 4.0), (2.0, 3.0), (1.0, 2.0), (0.0, 1.0)]:
        rating_count_result = await db.execute(
            select(func.count(Product.id))
            .where(Product.is_active == True)
            .where(Product.rating >= min_r, Product.rating < max_r)
        )
        count = rating_count_result.scalar_one() or 0
        if count > 0:
            rating_ranges.append(RatingFacetBucket(
                min_rating=min_r,
                max_rating=max_r,
                count=count,
            ))

    response = SearchFiltersResponse(
        categories=categories,
        brands=brands,
        platforms=platforms,
        countries=countries,
        price_ranges=price_ranges,
        rating_ranges=rating_ranges,
        price_min=Decimal(str(price_min)),
        price_max=Decimal(str(price_max)),
    )

    await cache.cache_set(cache_key, response.model_dump(mode="json"), ttl_seconds=300)
    return response


MAX_SEARCH_HISTORY = 100


@router.get("/history", response_model=SearchHistoryListResponse, summary="Get search history for the authenticated API key")
@limiter.limit("60/minute")
async def get_search_history(
    request: Request,
    limit: int = Query(20, ge=1, le=100, description="Results per page (1-100)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> SearchHistoryListResponse:
    request.state.api_key = api_key

    count_result = await db.execute(
        select(func.count(SearchHistory.id)).where(
            SearchHistory.developer_id == api_key.developer_id,
        )
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(SearchHistory)
        .where(SearchHistory.developer_id == api_key.developer_id)
        .order_by(SearchHistory.created_at.desc())
        .limit(min(limit, MAX_SEARCH_HISTORY))
        .offset(offset)
    )
    searches = result.scalars().all()

    return SearchHistoryListResponse(
        searches=[SearchHistoryEntry.model_validate(s) for s in searches],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(searches)) < total,
    )
