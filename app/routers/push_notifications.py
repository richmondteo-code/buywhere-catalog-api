"""Push notifications router for browser push notification subscriptions."""
import uuid
import base64
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from pywebpush import webpush, Vapid
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_api_key
from app.database import get_db
from app.models.product import ApiKey
from app.models.push_subscription import PushSubscription
from app.config import get_settings

router = APIRouter(prefix="/v1/push", tags=["push"])

settings = get_settings()


class PushSubscriptionRequest(BaseModel):
    endpoint: str
    p256dh: str = Field(..., description="Browser push subscription p256dh key")
    auth: str = Field(..., description="Browser push subscription auth key")
    user_id: Optional[str] = None


class PushSubscriptionResponse(BaseModel):
    id: str
    endpoint: str
    is_active: bool
    created_at: datetime


class VapidKeyResponse(BaseModel):
    public_key: str


@router.get("/vapid-key", response_model=VapidKeyResponse, summary="Get VAPID public key for browser subscription")
async def get_vapid_key():
    """Return the VAPID public key for browsers to use when subscribing."""
    if not settings.web_push_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Push notifications are not enabled",
        )
    
    if not settings.web_push_vapid_public_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VAPID keys not configured",
        )
    
    return VapidKeyResponse(public_key=settings.web_push_vapid_public_key)


@router.post("/subscribe", response_model=PushSubscriptionResponse, status_code=status.HTTP_201_CREATED, summary="Subscribe to push notifications")
async def subscribe_to_push(
    request: Request,
    body: PushSubscriptionRequest,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> PushSubscriptionResponse:
    """Subscribe a browser to push notifications."""
    if not settings.web_push_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Push notifications are not enabled",
        )
    
    user_id = body.user_id or api_key.developer_id
    
    existing = await db.execute(
        select(PushSubscription).where(
            PushSubscription.endpoint == body.endpoint,
        )
    )
    existing_sub = existing.scalar_one_or_none()
    
    if existing_sub:
        existing_sub.p256dh = body.p256dh
        existing_sub.auth = body.auth
        existing_sub.user_id = user_id
        existing_sub.is_active = True
        existing_sub.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing_sub)
        return PushSubscriptionResponse(
            id=existing_sub.id,
            endpoint=existing_sub.endpoint,
            is_active=existing_sub.is_active,
            created_at=existing_sub.created_at,
        )
    
    sub_id = str(uuid.uuid4())
    sub = PushSubscription(
        id=sub_id,
        user_id=user_id,
        endpoint=body.endpoint,
        p256dh=body.p256dh,
        auth=body.auth,
        is_active=True,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    
    return PushSubscriptionResponse(
        id=sub.id,
        endpoint=sub.endpoint,
        is_active=sub.is_active,
        created_at=sub.created_at,
    )


@router.delete("/unsubscribe", status_code=status.HTTP_204_NO_CONTENT, summary="Unsubscribe from push notifications")
async def unsubscribe_from_push(
    request: Request,
    endpoint: str,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
):
    """Unsubscribe a browser from push notifications."""
    if not settings.web_push_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Push notifications are not enabled",
        )
    
    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.endpoint == endpoint,
        )
    )
    sub = result.scalar_one_or_none()
    
    if sub:
        sub.is_active = False
        sub.updated_at = datetime.utcnow()
        await db.commit()
    
    return None


@router.get("/subscriptions", summary="List push subscriptions")
async def list_subscriptions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
):
    """List all push subscriptions for the current API key."""
    if not settings.web_push_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Push notifications are not enabled",
        )
    
    result = await db.execute(
        select(func.count(PushSubscription.id)).where(
            PushSubscription.user_id == api_key.developer_id,
            PushSubscription.is_active.is_(True),
        )
    )
    count = result.scalar() or 0
    
    return {"count": count, "subscriptions": []}
