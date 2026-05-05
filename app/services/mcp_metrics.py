from datetime import datetime, timezone, timedelta, date
from typing import Any

from sqlalchemy import select, func, text, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.query_log import QueryLog


class MCPMetricsAggregator:
    MCP_PATH_PREFIX = "/mcp/"

    async def aggregate_daily(
        self, db: AsyncSession, target_date: date | None = None,
    ) -> dict[str, Any]:
        if target_date is None:
            target_date = datetime.now(timezone.utc).date() - timedelta(days=1)

        day_start = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
        day_end = datetime.combine(target_date, datetime.max.time(), tzinfo=timezone.utc)

        total = await self._count_mcp_calls(db, day_start, day_end)
        per_tool = await self._count_per_tool(db, day_start, day_end)
        by_status = await self._status_distribution(db, day_start, day_end)
        latency = await self._latency_stats(db, day_start, day_end)
        unique_keys = await self._unique_api_keys(db, day_start, day_end)
        by_ai_model = await self._count_by_ai_model(db, day_start, day_end)
        by_region = await self._count_by_region(db, day_start, day_end)
        zero_result = await self._zero_result_count(db, day_start, day_end)
        error_count = sum(v for k, v in by_status.items() if int(k) >= 500)

        return {
            "date": target_date.isoformat(),
            "total_mcp_calls": total,
            "error_count": error_count,
            "error_rate": round(error_count / total * 100, 2) if total > 0 else 0.0,
            "success_rate": round((total - error_count) / total * 100, 2) if total > 0 else 0.0,
            "per_tool": per_tool,
            "by_status_code": by_status,
            "by_ai_model": by_ai_model,
            "by_region": by_region,
            "zero_result": zero_result,
            "latency_ms": latency,
            "unique_api_keys": unique_keys,
        }

    async def _count_mcp_calls(
        self, db: AsyncSession, start: datetime, end: datetime,
    ) -> int:
        result = await db.execute(
            select(func.count(QueryLog.id))
            .where(QueryLog.path.startswith(self.MCP_PATH_PREFIX))
            .where(QueryLog.created_at >= start)
            .where(QueryLog.created_at < end)
        )
        return result.scalar() or 0

    async def _count_per_tool(
        self, db: AsyncSession, start: datetime, end: datetime,
    ) -> dict[str, int]:
        result = await db.execute(
            select(
                func.coalesce(QueryLog.mcp_tool_name, QueryLog.path).label("tool"),
                func.count(QueryLog.id).label("cnt"),
            )
            .where(QueryLog.path.startswith(self.MCP_PATH_PREFIX))
            .where(QueryLog.created_at >= start)
            .where(QueryLog.created_at < end)
            .group_by(text("tool"))
            .order_by(text("cnt DESC"))
        )
        return {row.tool: row.cnt for row in result.all()}

    async def _status_distribution(
        self, db: AsyncSession, start: datetime, end: datetime,
    ) -> dict[str, int]:
        result = await db.execute(
            select(
                func.cast(QueryLog.status_code, text("text")).label("code"),
                func.count(QueryLog.id).label("cnt"),
            )
            .where(QueryLog.path.startswith(self.MCP_PATH_PREFIX))
            .where(QueryLog.created_at >= start)
            .where(QueryLog.created_at < end)
            .group_by(QueryLog.status_code)
            .order_by(QueryLog.status_code)
        )
        return {str(row.code): row.cnt for row in result.all()}

    async def _latency_stats(
        self, db: AsyncSession, start: datetime, end: datetime,
    ) -> dict[str, float | None]:
        result = await db.execute(
            select(
                func.avg(QueryLog.duration_ms).label("avg"),
                func.percentile_cont(0.50).within_group(QueryLog.duration_ms.asc()).label("p50"),
                func.percentile_cont(0.95).within_group(QueryLog.duration_ms.asc()).label("p95"),
                func.percentile_cont(0.99).within_group(QueryLog.duration_ms.asc()).label("p99"),
                func.min(QueryLog.duration_ms).label("min"),
                func.max(QueryLog.duration_ms).label("max"),
            )
            .where(QueryLog.path.startswith(self.MCP_PATH_PREFIX))
            .where(QueryLog.created_at >= start)
            .where(QueryLog.created_at < end)
        )
        row = result.one()
        if row.avg is None:
            return {"avg": None, "p50": None, "p95": None, "p99": None, "min": None, "max": None}
        return {
            "avg": round(float(row.avg), 2),
            "p50": round(float(row.p50), 2) if row.p50 else None,
            "p95": round(float(row.p95), 2) if row.p95 else None,
            "p99": round(float(row.p99), 2) if row.p99 else None,
            "min": round(float(row.min), 2),
            "max": round(float(row.max), 2),
        }

    async def _unique_api_keys(
        self, db: AsyncSession, start: datetime, end: datetime,
    ) -> int:
        result = await db.execute(
            select(func.count(func.distinct(QueryLog.api_key_id)))
            .where(QueryLog.path.startswith(self.MCP_PATH_PREFIX))
            .where(QueryLog.created_at >= start)
            .where(QueryLog.created_at < end)
            .where(QueryLog.api_key_id.isnot(None))
        )
        return result.scalar() or 0

    async def _count_by_ai_model(
        self, db: AsyncSession, start: datetime, end: datetime,
    ) -> dict[str, int]:
        result = await db.execute(
            select(
                func.coalesce(QueryLog.ai_model, "unknown").label("model"),
                func.count(QueryLog.id).label("cnt"),
            )
            .where(QueryLog.path.startswith(self.MCP_PATH_PREFIX))
            .where(QueryLog.created_at >= start)
            .where(QueryLog.created_at < end)
            .group_by(text("model"))
            .order_by(text("cnt DESC"))
        )
        return {row.model: row.cnt for row in result.all()}

    async def _count_by_region(
        self, db: AsyncSession, start: datetime, end: datetime,
    ) -> dict[str, int]:
        result = await db.execute(
            select(
                func.coalesce(QueryLog.region, "unknown").label("r"),
                func.count(QueryLog.id).label("cnt"),
            )
            .where(QueryLog.path.startswith(self.MCP_PATH_PREFIX))
            .where(QueryLog.created_at >= start)
            .where(QueryLog.created_at < end)
            .group_by(text("r"))
            .order_by(text("cnt DESC"))
        )
        return {row.r: row.cnt for row in result.all()}

    async def _zero_result_count(
        self, db: AsyncSession, start: datetime, end: datetime,
    ) -> dict[str, Any]:
        total = await self._count_mcp_calls(db, start, end)
        zero = await db.execute(
            select(func.count(QueryLog.id))
            .where(QueryLog.path.startswith(self.MCP_PATH_PREFIX))
            .where(QueryLog.created_at >= start)
            .where(QueryLog.created_at < end)
            .where(QueryLog.result_count == 0)
        )
        zero_count = zero.scalar() or 0
        return {
            "count": zero_count,
            "rate_pct": round(zero_count / total * 100, 2) if total > 0 else 0.0,
        }
