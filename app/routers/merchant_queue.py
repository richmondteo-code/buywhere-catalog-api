from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi import status as http_status
from sqlalchemy import func, select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_api_key
from app.database import get_db
from app.models.product import ApiKey, MerchantQueue
from app.schemas.merchant_queue import (
    MerchantQueueCreate,
    MerchantQueueUpdate,
    MerchantQueueClaim,
    MerchantQueueResponse,
    MerchantQueueStatus,
    MerchantQueueList,
)
from app.rate_limit import limiter
from app.logging_centralized import get_logger

logger = get_logger("merchant-queue")
router = APIRouter(prefix="/ingest/queue", tags=["merchant-queue"])


def _to_response(mq: MerchantQueue) -> MerchantQueueResponse:
    return MerchantQueueResponse(
        id=mq.id,
        domain=mq.domain,
        platform=mq.platform,
        vertical=mq.vertical,
        country=mq.country,
        status=mq.status,
        assigned_agent=mq.assigned_agent,
        discovered_at=mq.discovered_at,
        validated_at=mq.validated_at,
        error_message=mq.error_message,
        attempt_count=mq.attempt_count,
        metadata=mq.metadata_,
        claimed_at=mq.claimed_at,
        completed_at=mq.completed_at,
        created_at=mq.created_at,
        updated_at=mq.updated_at,
    )


@router.post("", response_model=MerchantQueueResponse, summary="Enqueue a validated merchant")
@limiter.limit("60/minute")
async def enqueue_merchant(
    request: Request,
    body: MerchantQueueCreate,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
):
    request.state.api_key = api_key

    existing_result = await db.execute(
        select(MerchantQueue).where(
            MerchantQueue.domain == body.domain,
            MerchantQueue.platform == body.platform,
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Domain {body.domain} is already queued for platform {body.platform}",
        )

    now = datetime.now(timezone.utc)
    entry = MerchantQueue(
        domain=body.domain,
        platform=body.platform,
        vertical=body.vertical,
        country=body.country,
        status=MerchantQueueStatus.pending.value,
        discovered_at=body.discovered_at or now,
        validated_at=body.validated_at or now,
        metadata_=body.metadata,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    logger.info("Merchant enqueued", extra={"domain": body.domain, "platform": body.platform})
    return _to_response(entry)


@router.get("", response_model=MerchantQueueList, summary="List queue entries")
@limiter.limit("60/minute")
async def list_queue(
    request: Request,
    status: Optional[str] = Query(default=None),
    platform: Optional[str] = Query(default=None),
    country: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
):
    request.state.api_key = api_key

    base_query = select(MerchantQueue)
    count_query = select(func.count(MerchantQueue.id))

    if status:
        base_query = base_query.where(MerchantQueue.status == status)
        count_query = count_query.where(MerchantQueue.status == status)
    if platform:
        base_query = base_query.where(MerchantQueue.platform == platform)
        count_query = count_query.where(MerchantQueue.platform == platform)
    if country:
        base_query = base_query.where(MerchantQueue.country == country.upper())
        count_query = count_query.where(MerchantQueue.country == country.upper())

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    result = await db.execute(
        base_query.order_by(MerchantQueue.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = result.scalars().all()

    return MerchantQueueList(
        total=total,
        limit=limit,
        offset=offset,
        items=[_to_response(item) for item in items],
    )


@router.get("/next", response_model=MerchantQueueResponse, summary="Claim next pending merchant")
@limiter.limit("30/minute")
async def claim_next(
    request: Request,
    agent: str = Query(..., min_length=1, max_length=128),
    platform: Optional[str] = Query(default=None),
    country: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
):
    request.state.api_key = api_key

    next_query = select(MerchantQueue).where(
        MerchantQueue.status == MerchantQueueStatus.pending.value
    )
    if platform:
        next_query = next_query.where(MerchantQueue.platform == platform)
    if country:
        next_query = next_query.where(MerchantQueue.country == country.upper())

    next_query = next_query.order_by(MerchantQueue.created_at.asc()).limit(1).with_for_update(skip_locked=True)

    result = await db.execute(next_query)
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="No pending merchants in the queue",
        )

    entry.status = MerchantQueueStatus.in_progress.value
    entry.assigned_agent = agent
    entry.claimed_at = datetime.now(timezone.utc)
    entry.attempt_count = (entry.attempt_count or 0) + 1
    await db.commit()
    await db.refresh(entry)

    logger.info("Merchant claimed", extra={"domain": entry.domain, "agent": agent})
    return _to_response(entry)


@router.get("/{entry_id}", response_model=MerchantQueueResponse, summary="Get queue entry by ID")
@limiter.limit("60/minute")
async def get_entry(
    request: Request,
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
):
    request.state.api_key = api_key

    result = await db.execute(
        select(MerchantQueue).where(MerchantQueue.id == entry_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Queue entry {entry_id} not found",
        )

    return _to_response(entry)


@router.patch("/{entry_id}", response_model=MerchantQueueResponse, summary="Update queue entry status")
@limiter.limit("60/minute")
async def update_entry(
    request: Request,
    entry_id: int,
    body: MerchantQueueUpdate,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
):
    request.state.api_key = api_key

    result = await db.execute(
        select(MerchantQueue).where(MerchantQueue.id == entry_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Queue entry {entry_id} not found",
        )

    update_data = body.model_dump(exclude_unset=True)

    if "status" in update_data:
        status_value = update_data["status"]
        if hasattr(status_value, "value"):
            status_value = status_value.value
        entry.status = status_value
        if status_value in (MerchantQueueStatus.done.value, MerchantQueueStatus.failed.value):
            entry.completed_at = datetime.now(timezone.utc)

    if "assigned_agent" in update_data:
        entry.assigned_agent = update_data["assigned_agent"]
    if "error_message" in update_data:
        entry.error_message = update_data["error_message"]
    if "metadata" in update_data:
        entry.metadata_ = update_data["metadata"]
    if "validated_at" in update_data:
        entry.validated_at = update_data["validated_at"]

    await db.commit()
    await db.refresh(entry)

    logger.info("Queue entry updated", extra={"entry_id": entry_id, "status": entry.status})
    return _to_response(entry)


@router.delete("/{entry_id}", summary="Remove queue entry")
@limiter.limit("30/minute")
async def delete_entry(
    request: Request,
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
):
    request.state.api_key = api_key

    result = await db.execute(
        select(MerchantQueue).where(MerchantQueue.id == entry_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Queue entry {entry_id} not found",
        )

    await db.delete(entry)
    await db.commit()

    logger.info("Queue entry deleted", extra={"entry_id": entry_id})
    return {"message": "Queue entry deleted", "id": entry_id}
