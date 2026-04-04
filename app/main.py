import logging
import uuid
from contextlib import asynccontextmanager
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
from app.routers import products, categories, keys, deals, ingestion, ingest, search, status, catalog, agents, analytics, admin, developers, webhooks, metrics
from app.graphql import graphql_router

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
    docs_url="/docs",
    redoc_url="/redoc",
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

# Routers
app.include_router(products.router)
app.include_router(search.router)
app.include_router(categories.router)
app.include_router(keys.router)
app.include_router(developers.router)
app.include_router(deals.router)
app.include_router(graphql_router, prefix="/graphql")
app.include_router(ingestion.router)
app.include_router(ingest.router)
app.include_router(status.router)
app.include_router(catalog.router)
app.include_router(agents.router)
app.include_router(analytics.router)
app.include_router(admin.router)
app.include_router(webhooks.router)
app.include_router(metrics.router)


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


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "version": settings.app_version, "environment": settings.environment}


@app.get("/v1", tags=["system"])
async def api_root():
    return {
        "api": "BuyWhere Catalog API",
        "version": "v1",
        "endpoints": {
            "search": "GET /v1/search",
            "products": "GET /v1/products",
            "best_price": "GET /v1/products/best-price",
            "compare_search": "GET /v1/products/compare?q=<query>",
            "compare_matrix": "POST /v1/products/compare",
            "compare_diff": "POST /v1/products/compare/diff",
            "trending": "GET /v1/products/trending",
            "export": "GET /v1/products/export?format=csv|json",
            "product": "GET /v1/products/{id}",
            "price_history": "GET /v1/products/{id}/price-history",
            "price_stats": "GET /v1/products/{id}/price-stats",
            "track_click": "POST /v1/products/{id}/click",
            "categories": "GET /v1/categories",
            "categories_taxonomy": "GET /v1/categories/taxonomy",
            "categories_products": "GET /v1/categories/{id}/products",
            "deals": "GET /v1/deals",
            "deals_price_drops": "GET /v1/deals/price-drops",
            "graphql": "POST /graphql",
            "graphql_playground": "GET /graphql",
            "ingestion": "POST /v1/ingestion",
            "ingest": "POST /v1/ingest/products",
            "status": "GET /v1/status",
            "metrics": "GET /v1/metrics",
            "catalog_health": "GET /v1/catalog/health",
            "click_analytics": "GET /v1/analytics/clicks",
            "admin_stats": "GET /v1/admin/stats",
            "developer_signup": "POST /v1/developers/signup",
            "developer_me": "GET /v1/developers/me",
            "webhooks_create": "POST /v1/webhooks",
            "webhooks_list": "GET /v1/webhooks",
            "webhooks_delete": "DELETE /v1/webhooks/{id}",
            "webhooks_test": "POST /v1/webhooks/test",
        },
        "auth": "Bearer token required (API key)",
        "docs": "/docs",
    }
