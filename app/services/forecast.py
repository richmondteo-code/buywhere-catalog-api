"""Revenue forecast service using simple linear projection."""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.affiliate import AffiliateCommission

logger = logging.getLogger("buywhere_api")


async def get_trailing_30day_avg(
    db: AsyncSession,
    network: Optional[str] = None,
) -> dict[str, Decimal]:
    """Calculate average daily commission (SGD) over trailing 30 days per network."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    query = select(
        AffiliateCommission.network,
        func.sum(AffiliateCommission.commission_amount_sgd).label("total_sgd"),
    ).where(
        and_(
            AffiliateCommission.timestamp >= cutoff,
            AffiliateCommission.commission_amount_sgd.isnot(None),
            AffiliateCommission.status == "approved",
        )
    )

    if network:
        query = query.where(AffiliateCommission.network == network)

    query = query.group_by(AffiliateCommission.network)

    result = await db.execute(query)
    rows = result.all()

    daily_avgs: dict[str, Decimal] = {}
    for row in rows:
        total = Decimal(str(row.total_sgd))
        daily_avgs[row.network] = (total / Decimal("30")).quantize(Decimal("0.01"))

    return daily_avgs


async def project_monthly_forecast(
    db: AsyncSession,
    months: int = 3,
    network: Optional[str] = None,
) -> list[dict]:
    """Project monthly revenue per network for the next N months."""
    daily_avgs = await get_trailing_30day_avg(db, network)

    today = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    results = []

    for net, daily_avg in daily_avgs.items():
        projected_monthly = (daily_avg * Decimal("30.4167")).quantize(Decimal("0.01"))
        monthly_projection = projected_monthly

        for i in range(months):
            projected_start = today + timedelta(days=30 * i)
            projected_end = today + timedelta(days=30 * (i + 1)) - timedelta(seconds=1)

            lower_bound = (monthly_projection * Decimal("0.8")).quantize(Decimal("0.01"))
            upper_bound = (monthly_projection * Decimal("1.2")).quantize(Decimal("0.01"))

            results.append({
                "network": net,
                "month": projected_start.strftime("%Y-%m"),
                "projected_start": projected_start.isoformat(),
                "projected_end": projected_end.isoformat(),
                "projected_revenue_sgd": float(monthly_projection),
                "confidence_interval": {
                    "lower_sgd": float(lower_bound),
                    "upper_sgd": float(upper_bound),
                },
            })

    return results
