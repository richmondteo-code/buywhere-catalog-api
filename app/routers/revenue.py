from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import func, select, and_, delete, case, text
from sqlalchemy.ext.asyncio import AsyncSession

import logging

from app.auth import get_current_api_key
from app.database import get_db
from app.models.affiliate import AffiliateCommission
from app.models.commission import CommissionDaily
from app.models.product import ApiKey
from app.rate_limit import limiter, rate_limit_from_request

logger = logging.getLogger("buywhere_api")

router = APIRouter(prefix="/v1/revenue", tags=["revenue"])


class DailyRevenueEntry(BaseModel):
    date: date
    network: str
    approved_amount_sgd: float
    approved_count: int
    pending_amount_sgd: float
    pending_count: int
    paid_amount_sgd: float
    paid_count: int
    total_amount_sgd: float
    total_count: int


class RevenueSummary(BaseModel):
    from_date: date
    to_date: date
    total_approved_sgd: float
    total_pending_sgd: float
    total_paid_sgd: float
    total_revenue_sgd: float
    approved_count: int
    pending_count: int
    paid_count: int
    network_count: int
    daily_avg_sgd: float


class NetworkBreakdown(BaseModel):
    network: str
    approved_amount_sgd: float
    approved_count: int
    pending_amount_sgd: float
    pending_count: int
    paid_amount_sgd: float
    paid_count: int
    total_amount_sgd: float
    total_count: int
    share_pct: float


class RevenueDailyResponse(BaseModel):
    from_date: date
    to_date: date
    days: list[DailyRevenueEntry]


class RevenueNetworksResponse(BaseModel):
    from_date: date
    to_date: date
    networks: list[NetworkBreakdown]


class AggregationResult(BaseModel):
    status: str
    rows_inserted: int
    message: str


@router.get("/summary", response_model=RevenueSummary, summary="Top-line revenue summary")
@limiter.limit(rate_limit_from_request)
async def get_revenue_summary(
    request: Request,
    from_date: Optional[date] = Query(None, description="Start date"),
    to_date: Optional[date] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
):
    request.state.api_key = api_key
    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=30)

    result = await db.execute(
        select(
            func.coalesce(func.sum(CommissionDaily.commission_amount_sgd).filter(CommissionDaily.status == "approved"), 0).label("approved"),
            func.coalesce(func.sum(CommissionDaily.commission_amount_sgd).filter(CommissionDaily.status == "pending"), 0).label("pending"),
            func.coalesce(func.sum(CommissionDaily.commission_amount_sgd).filter(CommissionDaily.status == "paid"), 0).label("paid"),
            func.coalesce(func.sum(CommissionDaily.commission_count).filter(CommissionDaily.status == "approved"), 0).label("approved_count"),
            func.coalesce(func.sum(CommissionDaily.commission_count).filter(CommissionDaily.status == "pending"), 0).label("pending_count"),
            func.coalesce(func.sum(CommissionDaily.commission_count).filter(CommissionDaily.status == "paid"), 0).label("paid_count"),
            func.count(func.distinct(CommissionDaily.network)).label("network_count"),
        ).where(
            CommissionDaily.date >= from_date,
            CommissionDaily.date <= to_date,
        )
    )
    row = result.one()
    total = float(row.approved + row.pending + row.paid)
    days_in_range = (to_date - from_date).days or 1

    return RevenueSummary(
        from_date=from_date,
        to_date=to_date,
        total_approved_sgd=float(row.approved),
        total_pending_sgd=float(row.pending),
        total_paid_sgd=float(row.paid),
        total_revenue_sgd=total,
        approved_count=int(row.approved_count),
        pending_count=int(row.pending_count),
        paid_count=int(row.paid_count),
        network_count=int(row.network_count),
        daily_avg_sgd=round(total / days_in_range, 2),
    )


@router.get("/daily", response_model=RevenueDailyResponse, summary="Daily revenue breakdown")
@limiter.limit(rate_limit_from_request)
async def get_daily_revenue(
    request: Request,
    from_date: Optional[date] = Query(None, description="Start date"),
    to_date: Optional[date] = Query(None, description="End date"),
    network: Optional[str] = Query(None, description="Filter by network"),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
):
    request.state.api_key = api_key
    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=30)

    conditions = [
        CommissionDaily.date >= from_date,
        CommissionDaily.date <= to_date,
    ]
    if network:
        conditions.append(CommissionDaily.network == network)

    rows_result = await db.execute(
        select(
            CommissionDaily.date,
            CommissionDaily.network,
            func.coalesce(func.sum(CommissionDaily.commission_amount_sgd).filter(CommissionDaily.status == "approved"), 0).label("approved_amount"),
            func.coalesce(func.sum(CommissionDaily.commission_count).filter(CommissionDaily.status == "approved"), 0).label("approved_count"),
            func.coalesce(func.sum(CommissionDaily.commission_amount_sgd).filter(CommissionDaily.status == "pending"), 0).label("pending_amount"),
            func.coalesce(func.sum(CommissionDaily.commission_count).filter(CommissionDaily.status == "pending"), 0).label("pending_count"),
            func.coalesce(func.sum(CommissionDaily.commission_amount_sgd).filter(CommissionDaily.status == "paid"), 0).label("paid_amount"),
            func.coalesce(func.sum(CommissionDaily.commission_count).filter(CommissionDaily.status == "paid"), 0).label("paid_count"),
        )
        .where(and_(*conditions))
        .group_by(CommissionDaily.date, CommissionDaily.network)
        .order_by(CommissionDaily.date.desc(), CommissionDaily.network)
    )
    rows = rows_result.all()

    return RevenueDailyResponse(
        from_date=from_date,
        to_date=to_date,
        days=[
            DailyRevenueEntry(
                date=r.date,
                network=r.network,
                approved_amount_sgd=float(r.approved_amount),
                approved_count=int(r.approved_count),
                pending_amount_sgd=float(r.pending_amount),
                pending_count=int(r.pending_count),
                paid_amount_sgd=float(r.paid_amount),
                paid_count=int(r.paid_count),
                total_amount_sgd=float(r.approved_amount + r.pending_amount + r.paid_amount),
                total_count=int(r.approved_count + r.pending_count + r.paid_count),
            )
            for r in rows
        ],
    )


@router.get("/networks", response_model=RevenueNetworksResponse, summary="Revenue breakdown by network")
@limiter.limit(rate_limit_from_request)
async def get_revenue_by_network(
    request: Request,
    from_date: Optional[date] = Query(None, description="Start date"),
    to_date: Optional[date] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
):
    request.state.api_key = api_key
    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=30)

    rows_result = await db.execute(
        select(
            CommissionDaily.network,
            func.coalesce(func.sum(CommissionDaily.commission_amount_sgd).filter(CommissionDaily.status == "approved"), 0).label("approved_amount"),
            func.coalesce(func.sum(CommissionDaily.commission_count).filter(CommissionDaily.status == "approved"), 0).label("approved_count"),
            func.coalesce(func.sum(CommissionDaily.commission_amount_sgd).filter(CommissionDaily.status == "pending"), 0).label("pending_amount"),
            func.coalesce(func.sum(CommissionDaily.commission_count).filter(CommissionDaily.status == "pending"), 0).label("pending_count"),
            func.coalesce(func.sum(CommissionDaily.commission_amount_sgd).filter(CommissionDaily.status == "paid"), 0).label("paid_amount"),
            func.coalesce(func.sum(CommissionDaily.commission_count).filter(CommissionDaily.status == "paid"), 0).label("paid_count"),
        )
        .where(
            CommissionDaily.date >= from_date,
            CommissionDaily.date <= to_date,
        )
        .group_by(CommissionDaily.network)
        .order_by(CommissionDaily.network)
    )
    rows = rows_result.all()

    total_all = sum(float(r.approved_amount + r.pending_amount + r.paid_amount) for r in rows) or 1

    return RevenueNetworksResponse(
        from_date=from_date,
        to_date=to_date,
        networks=[
            NetworkBreakdown(
                network=r.network,
                approved_amount_sgd=float(r.approved_amount),
                approved_count=int(r.approved_count),
                pending_amount_sgd=float(r.pending_amount),
                pending_count=int(r.pending_count),
                paid_amount_sgd=float(r.paid_amount),
                paid_count=int(r.paid_count),
                total_amount_sgd=float(r.approved_amount + r.pending_amount + r.paid_amount),
                total_count=int(r.approved_count + r.pending_count + r.paid_count),
                share_pct=round(float(r.approved_amount + r.pending_amount + r.paid_amount) / total_all * 100, 1),
            )
            for r in rows
        ],
    )


@router.post("/refresh", response_model=AggregationResult, summary="Aggregate daily commissions from raw data")
@limiter.limit(rate_limit_from_request)
async def refresh_daily_aggregation(
    request: Request,
    from_date: Optional[date] = Query(None, description="Start date (defaults to 90 days ago)"),
    to_date: Optional[date] = Query(None, description="End date (defaults to today)"),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
):
    request.state.api_key = api_key
    if api_key.tier not in ("enterprise", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=90)

    await db.execute(
        delete(CommissionDaily).where(
            CommissionDaily.date >= from_date,
            CommissionDaily.date <= to_date,
        )
    )

    raw_result = await db.execute(
        select(
            func.date(AffiliateCommission.earned_at).label("d"),
            AffiliateCommission.network,
            AffiliateCommission.status,
            func.count(AffiliateCommission.id).label("cnt"),
            func.sum(AffiliateCommission.commission_amount_sgd).label("total_sgd"),
            func.sum(AffiliateCommission.order_value_sgd).label("order_sgd"),
        )
        .where(
            AffiliateCommission.earned_at >= from_date,
            AffiliateCommission.earned_at < to_date + timedelta(days=1),
            AffiliateCommission.commission_amount_sgd.isnot(None),
        )
        .group_by(
            func.date(AffiliateCommission.earned_at),
            AffiliateCommission.network,
            AffiliateCommission.status,
        )
    )
    rows = raw_result.all()

    inserted = 0
    for r in rows:
        daily = CommissionDaily(
            date=r.d,
            network=r.network,
            status=r.status,
            commission_count=r.cnt or 0,
            commission_amount_sgd=r.total_sgd or Decimal("0.00"),
            order_value_sgd=r.order_sgd,
        )
        db.add(daily)
        inserted += 1

    await db.commit()
    return AggregationResult(
        status="ok",
        rows_inserted=inserted,
        message=f"Aggregated {inserted} daily rows from raw commissions ({from_date} to {to_date})",
    )
