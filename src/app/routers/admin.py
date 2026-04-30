"""admin router — cache invalidation, key revocation, and operational endpoints."""
import asyncio
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from typing import Optional

from app.config import get_settings
from app import cache

settings = get_settings()
ADMIN_SECRET = settings.jwt_secret_key

router = APIRouter(tags=["admin"])


class CacheInvalidateRequest(BaseModel):
    pattern: str
    key: Optional[str] = None


class CacheInvalidateResponse(BaseModel):
    deleted: int
    pattern: str


def _auth_admin(request: Request) -> None:
    secret = request.headers.get("x-admin-secret") or request.headers.get("admin_secret", "")
    if secret != ADMIN_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin secret")


@router.get("/admin/cache/stats")
async def admin_cache_stats(request: Request) -> dict:
    """Return Redis key count and memory info. Requires x-admin-secret header."""
    _auth_admin(request)
    key_count = await cache.get_cache_key_count()
    mem_info = await cache.get_redis_memory_info()
    return {"key_count": key_count, **mem_info}


@router.delete("/admin/cache", response_model=CacheInvalidateResponse)
async def admin_cache_invalidate(request: Request, body: CacheInvalidateRequest) -> CacheInvalidateResponse:
    """Delete all cache keys matching a pattern. Requires x-admin-secret header."""
    _auth_admin(request)
    if body.key:
        deleted = int(await cache.cache_delete(body.key))
    else:
        deleted = await cache.cache_delete_pattern(body.pattern)
    return CacheInvalidateResponse(deleted=deleted, pattern=body.pattern or body.key or "*")
