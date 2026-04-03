from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.affiliate_links import get_affiliate_url
from app.auth import get_current_api_key
from app.database import get_db
from app.models.product import ApiKey, Product
from app.rate_limit import limiter
from app.schemas.product import ProductListResponse, ProductResponse

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
@limiter.limit("1000/minute")
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
    # Store api_key on request.state for rate limiter
    request.state.api_key = api_key

    base_query = select(Product).where(Product.is_active == True)

    if q:
        # Full-text search using Postgres tsvector
        base_query = base_query.where(
            text("to_tsvector('english', title) @@ plainto_tsquery('english', :q)").bindparams(q=q)
        ).order_by(
            text("ts_rank(to_tsvector('english', title), plainto_tsquery('english', :q_rank)) DESC").bindparams(q_rank=q)
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

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginate
    results = await db.execute(base_query.limit(limit).offset(offset))
    products = results.scalars().all()

    return ProductListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[_map_product(p) for p in products],
    )


@router.get("/{product_id}", response_model=ProductResponse, summary="Get product by ID")
@limiter.limit("1000/minute")
async def get_product(
    request: Request,
    product_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> ProductResponse:
    request.state.api_key = api_key

    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.is_active == True)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    return _map_product(product)
