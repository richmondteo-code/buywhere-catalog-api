import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Union

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.rate_limit import limiter, TierRateLimitMiddleware, RedisPerMinuteRateLimitMiddleware
from app.request_logging import RequestLoggingMiddleware
from app.usage_metering import UsageMeteringMiddleware
from app.routers import products, categories, keys, deals, ingestion, ingest, search, status, catalog, agents, analytics, admin, developers, webhooks, metrics, alerts, images, changelog, feed, merchants, trending, export, enrichment, health, brands, watchlist, dedup, compare, billing, countries, sitemap, v2, merchant_analytics, affiliate, preferences, import_csv, saved_searches, usage, referrals, coupons, linkless_attribution
from app import clickthrough
from app.graphql import graphql_router
from app.versioning import VersionRoutingMiddleware
from app.services.health import get_db_health, check_disk_space, check_api_self_test
from app.services.scraper_health import get_scraper_health
from app.schemas.status import ComprehensiveHealthReport, DiskSpaceHealth, APIResponseTimeHealth

logger = logging.getLogger("buywhere_api")

settings = get_settings()

MAX_QUERY_LENGTH = 500


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="BuyWhere Catalog API",
    description=(
        "Agent-native product catalog API for AI agent commerce. "
        "Query millions of products across Southeast Asia."
    ),
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS - allow all origins for AI agents calling from anywhere
app.add_middleware(
    __import__("fastapi.middleware.cors", fromlist=["CORSMiddleware"]).CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RedisPerMinuteRateLimitMiddleware)
app.add_middleware(TierRateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(UsageMeteringMiddleware)

# API versioning middleware
app.add_middleware(VersionRoutingMiddleware)

# Routers — v1 under /v1 prefix, v2 under /v2 prefix
app.include_router(products.router, prefix="/v1")
app.include_router(search.router, prefix="/v1")
app.include_router(categories.router, prefix="/v1")
app.include_router(keys.router, prefix="/v1")
app.include_router(developers.router, prefix="/v1")
app.include_router(deals.router, prefix="/v1")
app.include_router(coupons.router, prefix="/v1")
app.include_router(graphql_router, prefix="/api/graphql")
app.include_router(ingestion.router, prefix="/v1")
app.include_router(ingest.router, prefix="/v1")
app.include_router(status.router, prefix="/v1")
app.include_router(catalog.router, prefix="/v1")
app.include_router(merchants.router, prefix="/v1")
app.include_router(merchant_analytics.router, prefix="/v1")
app.include_router(brands.router, prefix="/v1")
app.include_router(brands.sources_router, prefix="/v1")
app.include_router(agents.router)
app.include_router(analytics.router, prefix="/v1")
app.include_router(admin.router, prefix="/v1")
app.include_router(webhooks.router, prefix="/v1")
app.include_router(metrics.router, prefix="/v1")
app.include_router(alerts.router, prefix="/v1")
app.include_router(images.router, prefix="/v1")
app.include_router(changelog.router, prefix="/v1")
app.include_router(feed.router, prefix="/v1")
app.include_router(trending.router, prefix="/v1")
app.include_router(export.router, prefix="/v1")
app.include_router(enrichment.router, prefix="/v1")
app.include_router(health.router, prefix="/v1")
app.include_router(watchlist.router, prefix="/v1")
app.include_router(import_csv.router, prefix="/v1")
app.include_router(preferences.router, prefix="/v1")
app.include_router(countries.router, prefix="/v1")
app.include_router(dedup.router, prefix="/v1")
app.include_router(dedup.dedup_ingest_router, prefix="/v1")
app.include_router(compare.router, prefix="/v1")
app.include_router(affiliate.router, prefix="/v1")
app.include_router(billing.router, prefix="/v1")
app.include_router(usage.router, prefix="/v1")
app.include_router(sitemap.router)
app.include_router(v2.router)
app.include_router(saved_searches.router, prefix="/v1")
app.include_router(clickthrough.router)
app.include_router(referrals.router, prefix="/v1")
app.include_router(linkless_attribution.router, prefix="/v1")


def error_response(code: str, message: str, details: Union[dict, list, None] = None, status_code: int = 400):
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details or {}}},
    )


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return error_response("NOT_FOUND", "The requested resource was not found", status_code=404)
    return error_response(
        f"HTTP_{exc.status_code}",
        exc.detail if hasattr(exc, "detail") else "An error occurred",
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc not in ("body", "query", "path"))
        
        msg = error["msg"]
        error_type = error["type"]
        
        if error_type == "string_too_long":
            ctx = error.get("ctx", {})
            limit = ctx.get("limit_value", MAX_QUERY_LENGTH) if ctx else MAX_QUERY_LENGTH
            msg = f"String exceeds maximum length of {limit} characters"
        elif error_type == "missing":
            msg = f"Required parameter '{field}' is missing"
        elif error_type == "greater_than_equal":
            ctx = error.get("ctx", {})
            limit = ctx.get("limit_value", "") if ctx else ""
            msg = f"Value must be greater than or equal to {limit}"
        elif error_type == "less_than_equal":
            ctx = error.get("ctx", {})
            limit = ctx.get("limit_value", "") if ctx else ""
            msg = f"Value must be less than or equal to {limit}"
        elif error_type == "less_than":
            ctx = error.get("ctx", {})
            limit = ctx.get("limit_value", "") if ctx else ""
            msg = f"Value must be less than {limit}"
        elif error_type == "enum":
            ctx = error.get("ctx", {})
            expected = ctx.get("expected", []) if ctx else []
            msg = f"Invalid value. Expected one of: {', '.join(expected)}"
        
        errors.append({
            "field": field or "unknown",
            "message": msg,
            "type": error_type,
        })
    return error_response(
        "VALIDATION_ERROR",
        "Request validation failed",
        details={"errors": errors, "count": len(errors)},
        status_code=422
    )


MAX_QUERY_LENGTH = 500


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return error_response("INTERNAL_ERROR", "An internal server error occurred", status_code=500)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return error_response("RATE_LIMIT_EXCEEDED", "Rate limit exceeded", status_code=429)


@app.get("/v1/health", response_model=ComprehensiveHealthReport, tags=["system"], summary="Comprehensive health check with dependency status")
async def health_check(request: Request):
    from app.database import async_session
    from app.schemas.status import ScraperHealthReport, DBHealthReport

    async with async_session() as db:
        db_health_data = await get_db_health(db)
        disk_data = await check_disk_space()
        api_self_test = await check_api_self_test(db)
        scraper_data = await get_scraper_health(db)

    db_report = DBHealthReport(**db_health_data)
    disk_report = DiskSpaceHealth(**disk_data)
    api_report = APIResponseTimeHealth(**api_self_test)
    scraper_report = ScraperHealthReport(**scraper_data)

    overall_status = "healthy"
    if not db_report.ok or not disk_report.ok or not api_report.ok:
        overall_status = "unhealthy"
    elif not scraper_report.healthy_count == scraper_report.total_scrapers:
        overall_status = "degraded"

    return ComprehensiveHealthReport(
        generated_at=datetime.now(timezone.utc),
        overall_status=overall_status,
        db=db_report,
        disk=disk_report,
        api_self_test=api_report,
        scrapers=scraper_report,
    )


@app.get("/v1", tags=["system"])
async def api_root():
    return {
        "api": "BuyWhere Catalog API",
        "version": "v1",
        "endpoints": {
            "search": "GET /v1/search",
            "search_semantic": "GET /v1/search/semantic",
            "search_filters": "GET /v1/search/filters",
            "products": "GET /v1/products",
            "best_price": "GET /v1/products/best-price",
            "compare_search": "GET /v1/products/compare?q=<query>",
            "compare_matrix": "POST /v1/products/compare",
            "compare_diff": "POST /v1/products/compare/diff",
            "trending": "GET /v1/products/trending",
            "export": "GET /v1/products/export?format=csv|json",
            "feed": "GET /v1/products/feed?updatedSince=ISO8601",
            "feed_new": "GET /v1/feed/new",
            "feed_deals": "GET /v1/feed/deals",
            "feed_changes_sse": "GET /v1/feed/changes",
            "product": "GET /v1/products/{id}",
            "price_history": "GET /v1/products/{id}/price-history",
            "price_stats": "GET /v1/products/{id}/price-stats",
            "price_comparison": "GET /v1/products/{id}/price-comparison",
            "track_click": "POST /v1/products/{id}/click",
            "similar": "GET /v1/products/{id}/similar",
            "categories": "GET /v1/categories",
            "categories_taxonomy": "GET /v1/categories/taxonomy",
            "categories_products": "GET /v1/categories/{id}/products",
            "brands": "GET /v1/brands",
            "brands_products": "GET /v1/brands/{brand_name}/products",
            "countries": "GET /v1/countries",
            "sources": "GET /v1/sources",
            "deals": "GET /v1/deals",
            "deals_price_drops": "GET /v1/deals/price-drops",
            "graphql": "POST /api/graphql",
            "graphql_playground": "GET /api/graphql",
            "ingestion": "POST /v1/ingestion",
            "ingest": "POST /v1/ingest/products",
            "import_csv": "POST /v1/import/csv",
            "status": "GET /v1/status",
            "metrics": "GET /v1/metrics",
            "metrics_quality": "GET /v1/metrics/quality",
            "catalog_health": "GET /v1/catalog/health",
            "click_analytics": "GET /v1/analytics/clicks",
            "usage_analytics": "GET /v1/analytics/usage",
            "admin_stats": "GET /v1/admin/stats",
            "developer_signup": "POST /v1/developers/signup",
            "developer_me": "GET /v1/developers/me",
            "keys_create": "POST /v1/keys",
            "keys_list": "GET /v1/keys",
            "keys_revoke": "DELETE /v1/keys/{id}",
            "keys_rotate": "POST /v1/keys/{id}/rotate",
            "webhooks_create": "POST /v1/webhooks",
            "webhooks_list": "GET /v1/webhooks",
            "webhooks_delete": "DELETE /v1/webhooks/{id}",
            "webhooks_test": "POST /v1/webhooks/test",
            "alerts_create": "POST /v1/alerts",
            "alerts_list": "GET /v1/alerts",
            "alerts_delete": "DELETE /v1/alerts/{id}",
            "image_register": "POST /v1/images?url=...",
            "image_proxy": "GET /v1/images/{hash}?w=&h=&format=",
            "image_info": "GET /v1/images/{hash}/info",
            "changelog": "GET /v1/changelog",
            "billing_subscribe": "POST /v1/billing/subscribe",
            "billing_status": "GET /v1/billing/status",
            "billing_tiers": "GET /v1/billing/tiers",
            "usage": "GET /v1/usage",
            "sitemap": "GET /sitemap.xml",
            "robots": "GET /robots.txt",
        },
        "auth": "Bearer token required (API key)",
        "docs": "/api/docs",
        "versioning": "URI-based (/v1/*). Accept-Version header optional. v1 is deprecated - use v2.",
    }


@app.get("/dashboard", tags=["system"])
async def dashboard():
    from starlette.responses import FileResponse
    return FileResponse("templates/dashboard.html")

@app.get("/playground", tags=["system"])
async def playground():
    from starlette.responses import FileResponse
    return FileResponse("templates/playground.html")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    from starlette.responses import FileResponse
    return FileResponse("templates/swagger.html")


@app.get("/api/docs", include_in_schema=False)
async def api_swagger_ui():
    from starlette.responses import RedirectResponse
    return RedirectResponse(url="/docs")


@app.get("/status", tags=["system"])
async def status_page():
    from starlette.responses import FileResponse
    return FileResponse("static/status.html")
