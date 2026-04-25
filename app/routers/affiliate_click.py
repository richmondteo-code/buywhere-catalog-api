from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import bearer_scheme, decode_access_token
from app.affiliate_links import get_underlying_affiliate_url, parse_tracking_id, is_valid_url
from app.database import get_db
from app.models.product import ApiKey, Product
from app.models.affiliate import AffiliateClick, AffiliateConversion
from app.rate_limit import limiter
from app.logging_centralized import get_logger

logger = get_logger("affiliate-click-service")

router = APIRouter(prefix="/affiliate", tags=["affiliate"])


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def anonymize_ip(ip: str) -> str:
    if not ip or ip == "unknown":
        return ip
    try:
        parts = ip.split(".")
        if len(parts) == 4:
            return ".".join(parts[:3]) + ".0"
    except:
        pass
    return ip


async def get_optional_api_key(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiKey | None:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = decode_access_token(token)
        if payload and "key_id" in payload:
            key_id = payload["key_id"]
            result = await db.execute(
                select(ApiKey).where(ApiKey.id == key_id, ApiKey.is_active == True)
            )
            return result.scalar_one_or_none()
    return None


class AffiliateClickRequest(BaseModel):
    product_id: int
    session_id: str
    platform: Optional[str] = None
    merchant: Optional[str] = None
    tracking_id: Optional[str] = None
    agent_id: Optional[str] = None
    affiliate_partner: Optional[str] = None
    destination_url: Optional[str] = None
    referrer: Optional[str] = None


class AffiliateClickResponse(BaseModel):
    click_id: int
    redirect_url: str
    logged: bool


class AffiliateStatsRequest(BaseModel):
    session_id: Optional[str] = None
    merchant: Optional[str] = None
    platform: Optional[str] = None
    days: int = Query(30, ge=1, le=365)


class AffiliateClickStats(BaseModel):
    total_clicks: int
    unique_sessions: int
    by_platform: dict


class AffiliateConversionStats(BaseModel):
    total_conversions: int
    total_revenue: float
    currency: str
    by_platform: dict


class AffiliateStatsResponse(BaseModel):
    clicks: AffiliateClickStats
    conversions: AffiliateConversionStats


@router.post("/click", summary="Log affiliate click and redirect to merchant")
@limiter.limit("100/minute")
async def log_affiliate_click(
    request: Request,
    body: AffiliateClickRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey | None = Depends(get_optional_api_key),
):
    """Log an affiliate click and redirect to the merchant URL.
    
    This endpoint:
    1. Validates the product exists
    2. Logs the click to affiliate_clicks table
    3. Returns a 302 redirect to the merchant's affiliate URL
    """
    product_result = await db.execute(
        select(Product).where(Product.id == body.product_id, Product.is_active == True)
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    platform = body.platform or product.source
    merchant = body.merchant or product.merchant_id or product.source

    if body.tracking_id:
        parsed = parse_tracking_id(body.tracking_id)
        if parsed:
            product_id_from_tracking, _ = parsed
            if product_id_from_tracking == body.product_id:
                destination_url = get_underlying_affiliate_url(platform, product.url)
            else:
                destination_url = body.destination_url or product.url
        else:
            destination_url = body.destination_url or product.url
    else:
        destination_url = get_underlying_affiliate_url(platform, product.url)

    if not destination_url or not is_valid_url(destination_url):
        destination_url = product.url

    client_ip = anonymize_ip(get_client_ip(request))

    click_record = AffiliateClick(
        session_id=body.session_id,
        product_id=body.product_id,
        merchant=merchant,
        platform=platform,
        tracking_id=body.tracking_id,
        api_key_id=str(api_key.id) if api_key else None,
        agent_id=body.agent_id,
        affiliate_partner=body.affiliate_partner,
        destination_url=destination_url,
        referrer=body.referrer or request.headers.get("Referer"),
        user_agent=request.headers.get("User-Agent"),
        user_ip=client_ip,
        country=request.headers.get("CF-IPCountry") or request.headers.get("X-Country") or None,
    )
    db.add(click_record)
    await db.commit()
    await db.refresh(click_record)

    return RedirectResponse(url=destination_url, status_code=status.HTTP_302_FOUND)


@router.get("/stats", response_model=AffiliateStatsResponse, summary="Get affiliate revenue dashboard stats")
@limiter.limit("30/minute")
async def get_affiliate_stats(
    request: Request,
    session_id: str | None = Query(None, description="Filter by session ID"),
    merchant: str | None = Query(None, description="Filter by merchant"),
    platform: str | None = Query(None, description="Filter by platform"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_optional_api_key),
):
    """Get affiliate click and conversion statistics for the revenue dashboard.
    
    Returns click counts, unique sessions, and conversion metrics broken down by platform.
    """
    cutoff = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=days)

    clicks_query = select(
        func.count(AffiliateClick.id).label("total_clicks"),
        func.count(func.distinct(AffiliateClick.session_id)).label("unique_sessions"),
        AffiliateClick.platform,
    ).where(
        AffiliateClick.clicked_at >= cutoff
    )

    if session_id:
        clicks_query = clicks_query.where(AffiliateClick.session_id == session_id)
    if merchant:
        clicks_query = clicks_query.where(AffiliateClick.merchant == merchant)
    if platform:
        clicks_query = clicks_query.where(AffiliateClick.platform == platform)

    clicks_query = clicks_query.group_by(AffiliateClick.platform)
    clicks_result = await db.execute(clicks_query)
    clicks_rows = clicks_result.all()

    conversions_query = select(
        func.count(AffiliateConversion.id).label("total_conversions"),
        func.coalesce(func.sum(AffiliateConversion.conversion_revenue), 0).label("total_revenue"),
        AffiliateConversion.platform,
    ).where(
        AffiliateConversion.converted_at >= cutoff
    )

    if session_id:
        conversions_query = conversions_query.where(AffiliateConversion.session_id == session_id)
    if merchant:
        conversions_query = conversions_query.where(AffiliateConversion.merchant == merchant)
    if platform:
        conversions_query = conversions_query.where(AffiliateConversion.platform == platform)

    conversions_query = conversions_query.group_by(AffiliateConversion.platform)
    conversions_result = await db.execute(conversions_query)
    conversions_rows = conversions_result.all()

    by_platform_clicks = {}
    total_clicks = 0
    total_sessions = 0
    for row in clicks_rows:
        by_platform_clicks[row.platform or "unknown"] = {
            "clicks": row.total_clicks,
            "sessions": row.unique_sessions,
        }
        total_clicks += row.total_clicks
        total_sessions += row.unique_sessions

    by_platform_conversions = {}
    total_conversions = 0
    total_revenue = 0.0
    for row in conversions_rows:
        by_platform_conversions[row.platform or "unknown"] = {
            "conversions": row.total_conversions,
            "revenue": float(row.total_revenue or 0),
        }
        total_conversions += row.total_conversions
        total_revenue += float(row.total_revenue or 0)

    return AffiliateStatsResponse(
        clicks=AffiliateClickStats(
            total_clicks=total_clicks,
            unique_sessions=total_sessions,
            by_platform=by_platform_clicks,
        ),
        conversions=AffiliateConversionStats(
            total_conversions=total_conversions,
            total_revenue=total_revenue,
            currency="SGD",
            by_platform=by_platform_conversions,
        ),
    )


@router.post("/conversion", summary="Log an affiliate conversion event")
@limiter.limit("50/minute")
async def log_affiliate_conversion(
    request: Request,
    click_id: int,
    session_id: str,
    product_id: int,
    conversion_revenue: float | None = None,
    conversion_type: str | None = None,
    conversion_data: dict | None = None,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey | None = Depends(get_optional_api_key),
):
    """Log a conversion event for an affiliate click.
    
    This should be called when a user completes a purchase or other conversion action
    after clicking through an affiliate link.
    """
    click_result = await db.execute(
        select(AffiliateClick).where(AffiliateClick.id == click_id)
    )
    click = click_result.scalar_one_or_none()
    if not click:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Click not found")

    conversion_record = AffiliateConversion(
        click_id=click_id,
        session_id=session_id,
        product_id=product_id,
        merchant=click.merchant,
        platform=click.platform,
        tracking_id=click.tracking_id,
        api_key_id=str(api_key.id) if api_key else click.api_key_id,
        agent_id=click.agent_id,
        affiliate_partner=click.affiliate_partner,
        conversion_revenue=conversion_revenue,
        currency="SGD",
        conversion_type=conversion_type,
        conversion_data=conversion_data,
    )
    db.add(conversion_record)
    await db.commit()
    await db.refresh(conversion_record)

    return {"conversion_id": conversion_record.id, "logged": True}
