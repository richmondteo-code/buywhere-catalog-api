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
from app.rate_limit import limiter, rate_limit_from_request
from app.schemas.product import ProductListResponse, ProductResponse, SearchSuggestionResponse, SearchSuggestion, AutocompleteResponse, AutocompleteSuggestion
from app.affiliate_links import get_affiliate_url
from app.services.currency import SUPPORTED_CURRENCIES, convert_price, get_rate_for_header
from app import cache
from app.routers.search_i18n import translate_query

SUPPORTED_SEARCH_LANGS = ("ms", "th", "vi", "id", "en")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/search", tags=["search"])

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


def _map_product(p: Product, target_currency: Optional[str] = None) -> ProductResponse:
    price = p.price
    currency = p.currency or "SGD"
    if target_currency and target_currency != currency:
        converted = convert_price(price, currency, target_currency)
        if converted is not None:
            price = converted
            currency = target_currency
    return ProductResponse(
        id=p.id,
        sku=p.sku,
        source=p.source,
        merchant_id=p.merchant_id,
        name=p.title,
        description=p.description,
        price=price,
        currency=currency,
        buy_url=p.url,
        affiliate_url=get_affiliate_url(p.source, p.url, p.id) if p.url else None,
        image_url=p.image_url,
        brand=p.brand,
        category=p.category,
        category_path=p.category_path,
        rating=p.rating,
        is_available=p.is_active,
        metadata=p.metadata_,
        updated_at=p.updated_at,
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
        raise HTTPException(
            status_code=422,
            detail={
                "code": "QUERY_TOO_LONG",
                "field": "q",
                "message": f"Query exceeds maximum length of 500 characters (got {len(q)})",
                "max_length": 500,
                "actual_length": len(q),
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
        response = ProductListResponse(**cached)
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
            "ts_rank_cd(search_vector, websearch_to_tsquery('english', :q_rank), 32) DESC"
        ).bindparams(q_rank=q)
        base_query = base_query.order_by(
            bm25_rank,
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

    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    results = await db.execute(base_query.limit(limit).offset(offset))
    products = results.scalars().all()

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    if q:
        logger.info(
            "Search query=%r category=%r platform=%r elapsed_ms=%.2f total=%d",
            q, category, platform, elapsed_ms, total
        )

    target_currency = currency if currency else default_currency
    response = ProductListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[_map_product(p, target_currency) for p in products],
        has_more=(offset + limit) < total,
    )

    await cache.cache_set(cache_key, response.model_dump(mode="json"), ttl_seconds=600)

    if target_currency != default_currency:
        rate_header = get_rate_for_header(default_currency, target_currency)
        if rate_header:
            request.state.response_headers = {"X-Currency-Rate": f"{default_currency}->{target_currency}:{rate_header}"}

    return response


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
