"""In-memory + DB stats collector for CEO KPI counters (BUY-11951)."""
import time
import threading
from collections import defaultdict
from datetime import datetime, timezone, timedelta, date
from typing import Any

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.query_log import QueryLog
from app.models.product import Product, ApiKey, Developer
from app.models.growth import DeveloperActivation


_requests_total: int = 0
_requests_by_path: dict[str, int] = defaultdict(int)
_requests_by_status: dict[int, int] = defaultdict(int)
_requests_by_method: dict[str, int] = defaultdict(int)
_latencies: list[float] = []
_active_keys_seen: set[str] = set()
_lock = threading.Lock()
_MAX_LATENCY_SAMPLES = 10_000


def record_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    api_key_id: str | None = None,
) -> None:
    global _requests_total, _latencies
    with _lock:
        _requests_total += 1
        _requests_by_path[path] += 1
        _requests_by_status[status_code] += 1
        _requests_by_method[method] += 1
        _latencies.append(duration_ms)
        if len(_latencies) > _MAX_LATENCY_SAMPLES:
            _latencies = _latencies[-_MAX_LATENCY_SAMPLES:]
        if api_key_id:
            _active_keys_seen.add(api_key_id)


def get_inmemory_counts() -> dict[str, Any]:
    with _lock:
        sorted_latencies = sorted(_latencies)
        n = len(sorted_latencies)
        p50 = sorted_latencies[n // 2] if n else 0
        p95 = sorted_latencies[int(n * 0.95)] if n else 0
        p99 = sorted_latencies[int(n * 0.99)] if n else 0

        total_2xx = sum(v for k, v in _requests_by_status.items() if 200 <= k < 300)
        total_4xx = sum(v for k, v in _requests_by_status.items() if 400 <= k < 500)
        total_5xx = sum(v for k, v in _requests_by_status.items() if 500 <= k < 600)
        total = _requests_total

        return {
            "total_requests": total,
            "by_path": dict(_requests_by_path),
            "by_status": {str(k): v for k, v in _requests_by_status.items()},
            "by_method": dict(_requests_by_method),
            "latency_ms": {
                "p50": round(p50, 2),
                "p95": round(p95, 2),
                "p99": round(p99, 2),
            },
            "error_rate": {
                "4xx_pct": round(total_4xx / total * 100, 2) if total else 0.0,
                "5xx_pct": round(total_5xx / total * 100, 2) if total else 0.0,
            },
            "unique_api_keys_in_window": len(_active_keys_seen),
        }


class StatsAggregator:
    """Aggregates CEO KPI counters from the query_log table and product catalog."""

    async def api_usage_summary(
        self, db: AsyncSession, since: datetime | None = None,
    ) -> dict[str, Any]:
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(hours=24)
        total = await db.scalar(
            select(func.count(QueryLog.id)).where(QueryLog.created_at >= since)
        ) or 0
        error_4xx = await db.scalar(
            select(func.count(QueryLog.id))
            .where(QueryLog.created_at >= since, QueryLog.status_code.between(400, 499))
        ) or 0
        error_5xx = await db.scalar(
            select(func.count(QueryLog.id))
            .where(QueryLog.created_at >= since, QueryLog.status_code.between(500, 599))
        ) or 0
        unique_keys = await db.scalar(
            select(func.count(func.distinct(QueryLog.api_key_id)))
            .where(QueryLog.created_at >= since, QueryLog.api_key_id.isnot(None))
        ) or 0
        return {
            "total_requests": total,
            "errors_4xx": error_4xx,
            "errors_5xx": error_5xx,
            "unique_api_keys": unique_keys,
        }

    async def latency_stats(
        self, db: AsyncSession, since: datetime | None = None,
    ) -> dict[str, float | None]:
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(hours=24)
        result = await db.execute(
            select(
                func.avg(QueryLog.duration_ms).label("avg"),
                func.percentile_cont(0.50).within_group(QueryLog.duration_ms.asc()).label("p50"),
                func.percentile_cont(0.95).within_group(QueryLog.duration_ms.asc()).label("p95"),
                func.percentile_cont(0.99).within_group(QueryLog.duration_ms.asc()).label("p99"),
            )
            .where(QueryLog.created_at >= since)
        )
        row = result.one()
        if row.avg is None:
            return {"avg": None, "p50": None, "p95": None, "p99": None}
        return {
            "avg": round(float(row.avg), 2),
            "p50": round(float(row.p50), 2),
            "p95": round(float(row.p95), 2),
            "p99": round(float(row.p99), 2),
        }

    async def traffic_by_ai_model(
        self, db: AsyncSession, since: datetime | None = None,
    ) -> dict[str, int]:
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(hours=24)
        result = await db.execute(
            select(
                func.coalesce(QueryLog.ai_model, "unknown").label("model"),
                func.count(QueryLog.id).label("cnt"),
            )
            .where(QueryLog.created_at >= since)
            .group_by(text("model"))
            .order_by(text("cnt DESC"))
        )
        return {row.model: row.cnt for row in result.all()}

    async def traffic_by_region(
        self, db: AsyncSession, since: datetime | None = None,
    ) -> dict[str, int]:
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(hours=24)
        result = await db.execute(
            select(
                func.coalesce(QueryLog.region, "unknown").label("r"),
                func.count(QueryLog.id).label("cnt"),
            )
            .where(QueryLog.created_at >= since)
            .group_by(text("r"))
            .order_by(text("cnt DESC"))
        )
        return {row.r: row.cnt for row in result.all()}

    async def mcp_vs_rest_breakdown(
        self, db: AsyncSession, since: datetime | None = None,
    ) -> dict[str, Any]:
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(hours=24)
        mcp_count = await db.scalar(
            select(func.count(QueryLog.id))
            .where(QueryLog.created_at >= since, QueryLog.path.startswith("/mcp/"))
        ) or 0
        rest_count = await db.scalar(
            select(func.count(QueryLog.id))
            .where(QueryLog.created_at >= since, QueryLog.path.startswith("/v1/"))
        ) or 0
        total = mcp_count + rest_count
        return {
            "mcp": {"count": mcp_count, "pct": round(mcp_count / total * 100, 1) if total else 0.0},
            "rest": {"count": rest_count, "pct": round(rest_count / total * 100, 1) if total else 0.0},
        }

    async def catalog_summary(self, db: AsyncSession) -> dict[str, Any]:
        total_products = await db.scalar(select(func.count(Product.id))) or 0
        active_products = await db.scalar(
            select(func.count(Product.id)).where(Product.is_active == True)
        ) or 0
        products_by_source = await db.execute(
            select(Product.source, func.count(Product.id).label("cnt"))
            .where(Product.is_active == True)
            .group_by(Product.source)
            .order_by(text("cnt DESC"))
        )
        by_source = {row.source: row.cnt for row in products_by_source.all()}
        products_by_region = await db.execute(
            select(Product.region, func.count(Product.id).label("cnt"))
            .where(Product.is_active == True)
            .group_by(Product.region)
            .order_by(text("cnt DESC"))
        )
        by_region = {row.region: row.cnt for row in products_by_region.all()}
        return {
            "total_products": total_products,
            "active_products": active_products,
            "by_source": by_source,
            "by_region": by_region,
        }

    async def developer_summary(self, db: AsyncSession) -> dict[str, Any]:
        total_devs = await db.scalar(select(func.count(Developer.id))) or 0
        total_keys = await db.scalar(select(func.count(ApiKey.id))) or 0
        active_keys = await db.scalar(
            select(func.count(ApiKey.id)).where(ApiKey.is_active == True)
        ) or 0
        activated = await db.scalar(
            select(func.count(DeveloperActivation.id)).where(
                DeveloperActivation.first_query_at.isnot(None)
            )
        ) or 0
        return {
            "total_developers": total_devs,
            "total_api_keys": total_keys,
            "active_api_keys": active_keys,
            "activated_developers": activated,
            "activation_rate_pct": round(activated / total_devs * 100, 1) if total_devs else 0.0,
        }

    async def hourly_traffic(
        self, db: AsyncSession, hours: int = 24,
    ) -> list[dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = await db.execute(
            select(
                func.date_trunc("hour", QueryLog.created_at).label("hour"),
                func.count(QueryLog.id).label("cnt"),
            )
            .where(QueryLog.created_at >= cutoff)
            .group_by(text("hour"))
            .order_by(text("hour"))
        )
        return [
            {"hour": row.hour.isoformat(), "requests": row.cnt}
            for row in result.all()
        ]

    async def top_paths(
        self, db: AsyncSession, since: datetime | None = None, limit: int = 20,
    ) -> list[dict[str, Any]]:
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(hours=24)
        result = await db.execute(
            select(
                QueryLog.path,
                func.count(QueryLog.id).label("cnt"),
                func.avg(QueryLog.duration_ms).label("avg_ms"),
            )
            .where(QueryLog.created_at >= since)
            .group_by(QueryLog.path)
            .order_by(text("cnt DESC"))
            .limit(limit)
        )
        return [
            {"path": row.path, "requests": row.cnt, "avg_latency_ms": round(float(row.avg_ms), 2) if row.avg_ms else None}
            for row in result.all()
        ]


stats_aggregator = StatsAggregator()
