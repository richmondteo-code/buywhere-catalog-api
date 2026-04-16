import json
import re
import uuid
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_api_key, provision_api_key
from app.database import get_db
from app.models.product import ApiKey, Developer
from app.rate_limit import limiter
from app.request_logging import LOG_FILE
from app.schemas.product import (
    DeveloperSignupRequest, DeveloperSignupResponse,
    DeveloperMeResponse, DeveloperResponse, ApiKeyResponse,
    DeveloperUsageResponse, UsageStats, EndpointUsage,
)
from app.services import growth
from app.services.analytics import post_hog

router = APIRouter(prefix="/developers", tags=["developers"])

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def is_valid_email(email: str) -> bool:
    return EMAIL_REGEX.match(email) is not None


@router.post("/signup", response_model=DeveloperSignupResponse, summary="Developer self-service signup")
@limiter.limit("5/hour")
async def developer_signup(
    request: Request,
    body: DeveloperSignupRequest,
    db: AsyncSession = Depends(get_db),
) -> DeveloperSignupResponse:
    """Create a developer account and API key in a single request.
    
    Rate limited to 5 accounts per IP per hour. HN launch path: signup -> API key -> first query in < 2 minutes.
    Tracks growth experiment assignments and schedules onboarding email drip.
    """
    if not is_valid_email(body.email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email format",
        )

    existing = await db.execute(
        select(Developer).where(Developer.email == body.email.lower())
    )
    if existing.scalar_one_or_none():
        return DeveloperSignupResponse(
            developer_id=None,
            email=body.email.lower(),
            plan=None,
            key_id=None,
            raw_key=None,
            name=None,
            tier=None,
            message="If this email was registered, check your inbox for your API key.",
        )

    developer_id = str(uuid.uuid4())
    developer = Developer(
        id=developer_id,
        email=body.email.lower(),
        plan="free",
    )
    db.add(developer)

    raw_key, new_key = await provision_api_key(
        developer_id=developer_id,
        name=body.name,
        tier="basic",
        db=db,
    )

    await growth.track_signup(
        db=db,
        developer_id=developer_id,
        email=body.email.lower(),
        experiment_variant=body.experiment_variant,
        discovery_path=body.discovery_path,
        referrer=body.referrer,
        utm_source=body.utm_source,
        utm_medium=body.utm_medium,
        utm_campaign=body.utm_campaign,
        utm_content=body.utm_content,
        utm_term=body.utm_term,
    )

    post_hog.track_signup(
        developer_id=developer_id,
        email=body.email.lower(),
        experiment_variant=body.experiment_variant,
        discovery_path=body.discovery_path,
        referrer=body.referrer,
        utm_source=body.utm_source,
        utm_medium=body.utm_medium,
        utm_campaign=body.utm_campaign,
        utm_content=body.utm_content,
        utm_term=body.utm_term,
    )

    await growth.schedule_email_drip(
        db=db,
        developer_id=developer_id,
        email=body.email.lower(),
    )

    return DeveloperSignupResponse(
        developer_id=developer_id,
        email=body.email.lower(),
        plan="free",
        key_id=str(new_key.id),
        raw_key=raw_key,
        name=str(new_key.name),
        tier=str(new_key.tier),
        message="Store this key securely — it will not be shown again. This is your first API key.",
    )


@router.get("/me", response_model=DeveloperMeResponse, summary="Get developer profile")
async def developer_me(
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> DeveloperMeResponse:
    """Returns developer profile and all API keys associated with this account."""
    result = await db.execute(
        select(Developer).where(Developer.id == api_key.developer_id)
    )
    developer = result.scalar_one_or_none()

    if not developer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer not found",
        )

    keys_result = await db.execute(
        select(ApiKey).where(
            ApiKey.developer_id == api_key.developer_id,
            ApiKey.is_active is True,
        ).order_by(ApiKey.created_at.desc())
    )
    keys = keys_result.scalars().all()

    return DeveloperMeResponse(
        developer=DeveloperResponse.model_validate(developer),
        api_keys=[ApiKeyResponse.model_validate(k) for k in keys],
        total_keys=len(keys),
    )


def _get_quota_for_tier(tier: str) -> int:
    tier_quotas = {
        "basic": 10000,
        "standard": 100000,
        "premium": 1000000,
    }
    return tier_quotas.get(tier, 10000)


def _parse_usage_from_logs(key_id: str) -> tuple[dict, list, float]:
    requests_today = 0
    requests_this_week = 0
    requests_this_month = 0
    total_requests = 0
    endpoint_counts: dict[str, dict] = defaultdict(lambda: {"count": 0, "total_time": 0.0})
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    log_path = Path(LOG_FILE)
    if log_path.exists():
        try:
            with open(log_path, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("apiKeyId") != key_id:
                            continue
                        ts_str = entry.get("timestamp", "")
                        try:
                            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        except (ValueError, TypeError):
                            continue
                        total_requests += 1
                        if ts >= month_start:
                            requests_this_month += 1
                        if ts >= week_start:
                            requests_this_week += 1
                        if ts >= today_start:
                            requests_today += 1
                        path = entry.get("path", "unknown")
                        method = entry.get("method", "GET")
                        duration = float(entry.get("durationMs", 0) or 0)
                        key = f"{method} {path}"
                        endpoint_counts[key]["count"] += 1
                        endpoint_counts[key]["total_time"] += duration
                    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
                        continue
        except (FileNotFoundError, PermissionError, IOError):
            pass

    top_endpoints = []
    for endpoint, data in sorted(endpoint_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:10]:
        parts = endpoint.split(" ", 1)
        method = parts[0] if len(parts) > 1 else "GET"
        path = parts[1] if len(parts) > 1 else endpoint
        avg_time = data["total_time"] / data["count"] if data["count"] > 0 else 0.0
        top_endpoints.append(EndpointUsage(
            endpoint=path,
            method=method,
            count=data["count"],
            avg_response_time_ms=round(avg_time, 2),
        ))

    avg_response_time = 0.0
    total_count = sum(d["count"] for d in endpoint_counts.values())
    total_time = sum(d["total_time"] for d in endpoint_counts.values())
    if total_count > 0:
        avg_response_time = round(total_time / total_count, 2)

    return (
        {"today": requests_today, "week": requests_this_week, "month": requests_this_month, "total": total_requests},
        top_endpoints,
        avg_response_time,
    )


@router.get("/me/usage", response_model=DeveloperUsageResponse, summary="Get detailed usage statistics for authenticated developer")
async def developer_usage(
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> DeveloperUsageResponse:
    """Returns detailed usage statistics for the authenticated developer and API key.
    
    Includes:
    - Requests today / this week / this month / all time
    - Quota remaining and usage percentage
    - Top 10 endpoints by request count
    - Average response time
    - Alert status (80% quota threshold)
    """
    result = await db.execute(
        select(Developer).where(Developer.id == api_key.developer_id)
    )
    developer = result.scalar_one_or_none()
    if not developer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer not found",
        )

    usage_data, top_endpoints, avg_response_time = _parse_usage_from_logs(str(api_key.id))
    key_tier = str(api_key.tier)
    quota_limit = _get_quota_for_tier(key_tier)
    quota_used = usage_data["month"]
    quota_remaining = max(0, quota_limit - quota_used)
    quota_used_pct = (quota_used / quota_limit * 100) if quota_limit > 0 else 0.0
    alert_triggered = quota_used_pct >= 80.0

    usage = UsageStats(
        requests_today=usage_data["today"],
        requests_this_week=usage_data["week"],
        requests_this_month=usage_data["month"],
        total_requests=usage_data["total"],
        quota_limit=quota_limit,
        quota_remaining=quota_remaining,
        quota_used_pct=round(quota_used_pct, 2),
        top_endpoints=top_endpoints,
        avg_response_time_ms=avg_response_time,
        alert_triggered=alert_triggered,
    )

    alert_config = {
        "threshold_pct": 80.0,
        "alert_triggered": alert_triggered,
        "alert_message": f"You have used {quota_used_pct:.1f}% of your monthly quota." if alert_triggered else None,
    }

    return DeveloperUsageResponse(
        developer_id=str(api_key.developer_id),
        key_id=str(api_key.id),
        key_name=str(api_key.name),
        tier=key_tier,
        usage=usage,
        alert_config=alert_config,
    )