import json
from typing import Any, Optional
from redis.asyncio import Redis
from app.config import get_settings

settings = get_settings()

_redis: Optional[Redis] = None


async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None


async def cache_get(key: str) -> Optional[Any]:
    try:
        redis = await get_redis()
        data = await redis.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception:
        return None


async def cache_set(key: str, value: Any, ttl_seconds: int = 600) -> bool:
    try:
        redis = await get_redis()
        await redis.setex(key, ttl_seconds, json.dumps(value))
        return True
    except Exception:
        return False


async def cache_delete(key: str) -> bool:
    try:
        redis = await get_redis()
        await redis.delete(key)
        return True
    except Exception:
        return False


async def cache_get_many(keys: list[str]) -> dict[str, Any]:
    try:
        redis = await get_redis()
        if not keys:
            return {}
        result = await redis.mget(keys)
        return {k: json.loads(v) for k, v in zip(keys, result) if v}
    except Exception:
        return {}


async def cache_delete_pattern(pattern: str) -> int:
    try:
        redis = await get_redis()
        keys = []
        async for key in redis.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            return await redis.delete(*keys)
        return 0
    except Exception:
        return 0


def build_cache_key(prefix: str, **kwargs) -> str:
    sorted_params = sorted(kwargs.items())
    param_str = "&".join(f"{k}={v}" for k, v in sorted_params if v is not None)
    return f"{prefix}:{param_str}" if param_str else prefix