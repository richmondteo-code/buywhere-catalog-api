"""Affiliate payout report and revenue forecast endpoints."""

import csv
import io
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_api_key
from app.database import get_db
from app.models.product import ApiKey
from app.models.affiliate import AffiliateCommission
from app.services.forecast import project_monthly_forecast

logger = logging.getLogger("buywhere_api")

router = APIRouter(prefix="/v1/affiliate", tags=["affiliate"])


class NetworkBreakdown(BaseModel):
    network: str
    total_commissions_sgd: float
    approved_count: int
    pending_count: int
    rejected_count: int


class PayoutReportResponse(BaseModel):
    from_date: datetime
    to_date: datetime
    total_commissions_sgd: float
    total_approved_sgd: float
    total_pending_sgd: float
    total_rejected_sgd: float
    total_count: int
    approved_count: int
    pending_count: int
    rejected_count: int
    by_network: list[NetworkBreakdown]


class ForecastEntry(BaseModel):
    network: str
    month: str
    projected_start: str
    projected_end: str
    projected_revenue_sgd: float
    confidence_interval: dict


class ForecastResponse(BaseModel):
    months: int
    generated_at: datetime
    forecasts: list[ForecastEntry]


@router.get("/report", response_model=PayoutReportResponse, summary="Get affiliate payout report")
async def get_affiliate_report(
    request: Request,
    network: Optional[str] = Query(None, description="Filter by network (e.g. shopee_sg)"),
    from_date: Optional[datetime] = Query(None, description="Start date (ISO 8601)"),
    to_date: Optional[datetime] = Query(None, description="End date (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
):
    request.state.api_key = api_key

    if to_date is None:
        to_date = datetime.now(timezone.utc)
    if from_date is None:
        from_date = to_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    base_conditions = [
        AffiliateCommission.timestamp >= from_date,
        AffiliateCommission.timestamp <= to_date,
        AffiliateCommission.commission_amount_sgd.isnot(None),
    ]
    if network:
        base_conditions.append(AffiliateCommission.network == network)

    totals_query = select(
        func.sum(AffiliateCommission.commission_amount_sgd).label("total"),
        func.count(AffiliateCommission.id).label("count"),
        func.sum(
            case((AffiliateCommission.status == "approved", AffiliateCommission.commission_amount_sgd), else_=0)
        ).label("approved_total"),
        func.sum(
            case((AffiliateCommission.status == "pending", AffiliateCommission.commission_amount_sgd), else_=0)
        ).label("pending_total"),
        func.sum(
            case((AffiliateCommission.status == "rejected", AffiliateCommission.commission_amount_sgd), else_=0)
        ).label("rejected_total"),
        func.count(case((AffiliateCommission.status == "approved", 1))).label("approved_count"),
        func.count(case((AffiliateCommission.status == "pending", 1))).label("pending_count"),
        func.count(case((AffiliateCommission.status == "rejected", 1))).label("rejected_count"),
    ).where(and_(*base_conditions))

    totals_result = await db.execute(totals_query)
    totals = totals_result.one()

    network_query = select(
        AffiliateCommission.network,
        func.sum(AffiliateCommission.commission_amount_sgd).label("total"),
        func.count(case((AffiliateCommission.status == "approved", 1))).label("approved_count"),
        func.count(case((AffiliateCommission.status == "pending", 1))).label("pending_count"),
        func.count(case((AffiliateCommission.status == "rejected", 1))).label("rejected_count"),
    ).where(and_(*base_conditions)).group_by(AffiliateCommission.network)

    network_result = await db.execute(network_query)
    network_rows = network_result.all()

    accept_header = request.headers.get("accept", "")
    if "text/csv" in accept_header.lower():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "network", "total_commissions_sgd", "approved_count",
            "pending_count", "rejected_count"
        ])
        for row in network_rows:
            writer.writerow([
                row.network,
                float(row.total or 0),
                row.approved_count or 0,
                row.pending_count or 0,
                row.rejected_count or 0,
            ])
        writer.writerow([])
        writer.writerow([
            "TOTAL",
            float(totals.total or 0),
            totals.approved_count or 0,
            totals.pending_count or 0,
            totals.rejected_count or 0,
        ])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=affiliate_report_{from_date.date()}_{to_date.date()}.csv"},
        )

    return PayoutReportResponse(
        from_date=from_date,
        to_date=to_date,
        total_commissions_sgd=float(totals.total or 0),
        total_approved_sgd=float(totals.approved_total or 0),
        total_pending_sgd=float(totals.pending_total or 0),
        total_rejected_sgd=float(totals.rejected_total or 0),
        total_count=totals.count or 0,
        approved_count=totals.approved_count or 0,
        pending_count=totals.pending_count or 0,
        rejected_count=totals.rejected_count or 0,
        by_network=[
            NetworkBreakdown(
                network=r.network,
                total_commissions_sgd=float(r.total or 0),
                approved_count=r.approved_count or 0,
                pending_count=r.pending_count or 0,
                rejected_count=r.rejected_count or 0,
            )
            for r in network_rows
        ],
    )


@router.get("/forecast", response_model=ForecastResponse, summary="Get affiliate revenue forecast")
async def get_affiliate_forecast(
    request: Request,
    months: int = Query(3, ge=1, le=12, description="Number of months to forecast"),
    network: Optional[str] = Query(None, description="Filter by network"),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> ForecastResponse:
    request.state.api_key = api_key

    forecasts = await project_monthly_forecast(db, months=months, network=network)

    return ForecastResponse(
        months=months,
        generated_at=datetime.now(timezone.utc),
        forecasts=[
            ForecastEntry(**entry)
            for entry in forecasts
        ],
    )
