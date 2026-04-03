from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.rate_limit import limiter
from app.routers import products, categories, keys

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

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Routers
app.include_router(products.router)
app.include_router(categories.router)
app.include_router(keys.router)


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "version": settings.app_version, "environment": settings.environment}


@app.get("/v1", tags=["system"])
async def api_root():
    return {
        "api": "BuyWhere Catalog API",
        "version": "v1",
        "endpoints": {
            "search": "GET /v1/products",
            "product": "GET /v1/products/{id}",
            "categories": "GET /v1/categories",
        },
        "auth": "Bearer token required (API key)",
        "docs": "/docs",
    }
