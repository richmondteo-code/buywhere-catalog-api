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
from app.rate_limit import limiter, RateLimitHeadersMiddleware
from app.request_logging import RequestLoggingMiddleware
from app.routers import products, categories, keys, deals, ingestion, ingest, search, status, catalog, agents, analytics, admin, developers, webhooks, metrics, alerts, images, changelog, feed, merchants, trending, export, enrichment, health, brands, watchlist, dedup, compare, billing, countries, sitemap, v2, merchant_analytics, affiliate
from app.graphql import graphql_router
from app.versioning import VersionRoutingMiddleware
from app.services.health import get_db_health, check_disk_space, check_api_self_test
from app.services.scraper_health import get_scraper_health
from app.schemas.status import ComprehensiveHealthReport, DiskSpaceHealth, APIResponseTimeHealth

logger = logging.getLogger("buywhere_api")

settings = get_settings()


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
app.add_middleware(RateLimitHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# API versioning middleware
app.add_middleware(VersionRoutingMiddleware)

# Routers — all under /api/v1 prefix
app.include_router(products.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(keys.router, prefix="/api")
app.include_router(developers.router, prefix="/api")
app.include_router(deals.router, prefix="/api")
app.include_router(graphql_router, prefix="/api/graphql")
app.include_router(ingestion.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(status.router, prefix="/api")
app.include_router(catalog.router, prefix="/api")
app.include_router(merchants.router, prefix="/api")
app.include_router(merchant_analytics.router, prefix="/api")
app.include_router(brands.router, prefix="/api")
app.include_router(brands.sources_router, prefix="/api")
app.include_router(agents.router)
app.include_router(analytics.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(images.router, prefix="/api")
app.include_router(changelog.router, prefix="/api")
app.include_router(feed.router, prefix="/api")
app.include_router(trending.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(enrichment.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(watchlist.router, prefix="/api")
app.include_router(countries.router, prefix="/api")
app.include_router(dedup.router, prefix="/api")
app.include_router(dedup.dedup_ingest_router, prefix="/api")
app.include_router(compare.router, prefix="/api")
app.include_router(affiliate.router, prefix="/api")
app.include_router(billing.router, prefix="/api")
app.include_router(sitemap.router)
app.include_router(v2.router)


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
        errors.append({"field": field, "message": error["msg"], "type": error["type"]})
    return error_response("VALIDATION_ERROR", "Request validation failed", details={"errors": errors}, status_code=422)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return error_response("INTERNAL_ERROR", "An internal server error occurred", status_code=500)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return error_response("RATE_LIMIT_EXCEEDED", "Rate limit exceeded", status_code=429)


@app.get("/api/v1/health", response_model=ComprehensiveHealthReport, tags=["system"], summary="Comprehensive health check with dependency status")
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


@app.get("/api/v1", tags=["system"])
async def api_root():
    return {
        "api": "BuyWhere Catalog API",
        "version": "v1",
        "endpoints": {
            "search": "GET /api/v1/search",
            "products": "GET /api/v1/products",
            "best_price": "GET /api/v1/products/best-price",
            "compare_search": "GET /api/v1/products/compare?q=<query>",
            "compare_matrix": "POST /api/v1/products/compare",
            "compare_diff": "POST /api/v1/products/compare/diff",
            "trending": "GET /api/v1/products/trending",
            "export": "GET /api/v1/products/export?format=csv|json",
            "feed": "GET /api/v1/products/feed?updatedSince=ISO8601",
            "feed_new": "GET /api/v1/feed/new",
            "feed_deals": "GET /api/v1/feed/deals",
            "product": "GET /api/v1/products/{id}",
            "price_history": "GET /api/v1/products/{id}/price-history",
            "price_stats": "GET /api/v1/products/{id}/price-stats",
            "price_comparison": "GET /api/v1/products/{id}/price-comparison",
            "track_click": "POST /api/v1/products/{id}/click",
            "categories": "GET /api/v1/categories",
            "categories_taxonomy": "GET /api/v1/categories/taxonomy",
            "categories_products": "GET /api/v1/categories/{id}/products",
            "brands": "GET /api/v1/brands",
            "brands_products": "GET /api/v1/brands/{brand_name}/products",
            "countries": "GET /api/v1/countries",
            "sources": "GET /api/v1/sources",
            "deals": "GET /api/v1/deals",
            "deals_price_drops": "GET /api/v1/deals/price-drops",
            "graphql": "POST /api/graphql",
            "graphql_playground": "GET /api/graphql",
            "ingestion": "POST /api/v1/ingestion",
            "ingest": "POST /api/v1/ingest/products",
            "status": "GET /api/v1/status",
            "metrics": "GET /api/v1/metrics",
            "metrics_quality": "GET /api/v1/metrics/quality",
            "catalog_health": "GET /api/v1/catalog/health",
            "click_analytics": "GET /api/v1/analytics/clicks",
            "admin_stats": "GET /api/v1/admin/stats",
            "developer_signup": "POST /api/v1/developers/signup",
            "developer_me": "GET /api/v1/developers/me",
            "keys_create": "POST /api/v1/keys",
            "keys_list": "GET /api/v1/keys",
            "keys_revoke": "DELETE /api/v1/keys/{id}",
            "keys_rotate": "POST /api/v1/keys/{id}/rotate",
            "webhooks_create": "POST /api/v1/webhooks",
            "webhooks_list": "GET /api/v1/webhooks",
            "webhooks_delete": "DELETE /api/v1/webhooks/{id}",
            "webhooks_test": "POST /api/v1/webhooks/test",
            "alerts_create": "POST /api/v1/alerts",
            "alerts_list": "GET /api/v1/alerts",
            "alerts_delete": "DELETE /api/v1/alerts/{id}",
            "image_register": "POST /api/v1/images?url=...",
            "image_proxy": "GET /api/v1/images/{hash}?w=&h=&format=",
            "image_info": "GET /api/v1/images/{hash}/info",
            "changelog": "GET /api/v1/changelog",
            "billing_subscribe": "POST /api/v1/billing/subscribe",
            "billing_status": "GET /api/v1/billing/status",
            "billing_tiers": "GET /api/v1/billing/tiers",
            "sitemap": "GET /sitemap.xml",
            "robots": "GET /robots.txt",
        },
        "auth": "Bearer token required (API key)",
        "docs": "/api/docs",
        "versioning": "URI-based (/api/v1/*). Accept-Version header optional.",
    }


@app.get("/dashboard", tags=["system"])
async def dashboard():
    from starlette.responses import FileResponse
    return FileResponse("templates/dashboard.html")
