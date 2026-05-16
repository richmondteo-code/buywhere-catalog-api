"""Stripe webhook handler.

Handles:
- checkout.session.completed  → provision API key, set tier
- customer.subscription.updated → update tier on plan change
- customer.subscription.deleted → revoke paid key, provision free key
- invoice.payment_failed → log only (grace period handling in Phase 2)

Route: POST /webhook/stripe  (no /v1 prefix — registered at root level)
"""
import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import stripe
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.product import ApiKey
from app.logging_centralized import get_logger

logger = get_logger("stripe-webhook")
router = APIRouter()


# ---------------------------------------------------------------------------
# Key helpers
# ---------------------------------------------------------------------------

def _generate_api_key() -> str:
    """Return a new plaintext key: bw_live_ + 32 url-safe chars."""
    raw = secrets.token_urlsafe(32)[:32]
    return f"bw_live_{raw}"


def _hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def _tier_from_price_id(price_id: str, settings) -> str:
    if price_id == settings.stripe_starter_price_id:
        return "starter"
    if price_id == settings.stripe_pro_price_id:
        return "pro"
    return "free"


# ---------------------------------------------------------------------------
# Webhook endpoint
# ---------------------------------------------------------------------------

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    settings = get_settings()

    if not settings.stripe_secret_key:
        logger.error("STRIPE_SECRET_KEY not configured")
        raise HTTPException(status_code=503, detail="Stripe not configured")

    stripe.api_key = settings.stripe_secret_key

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not settings.stripe_webhook_secret:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=503, detail="Stripe webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        logger.warning("Stripe webhook signature verification failed")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    logger.info(f"Stripe webhook received: {event_type} id={event['id']}")

    async with AsyncSessionLocal() as db:
        try:
            if event_type == "checkout.session.completed":
                await _handle_checkout_completed(event["data"]["object"], db, settings)
            elif event_type == "customer.subscription.updated":
                await _handle_subscription_updated(event["data"]["object"], db, settings)
            elif event_type == "customer.subscription.deleted":
                await _handle_subscription_deleted(event["data"]["object"], db, settings)
            elif event_type == "invoice.payment_failed":
                _handle_payment_failed(event["data"]["object"])
            else:
                logger.debug(f"Unhandled Stripe event type: {event_type}")
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Error processing Stripe event {event_type}: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal error processing webhook")

    return JSONResponse({"received": True})


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

async def _handle_checkout_completed(session: dict, db: AsyncSession, settings) -> None:
    user_id = (session.get("metadata") or {}).get("user_id")
    if not user_id:
        logger.warning(f"checkout.session.completed missing user_id in metadata: {session.get('id')}")
        return

    stripe_customer_id = session.get("customer")
    stripe_subscription_id = session.get("subscription")

    # Determine tier from line items
    tier = "starter"
    try:
        if stripe_subscription_id:
            subscription = stripe.Subscription.retrieve(
                stripe_subscription_id, expand=["items.data.price"]
            )
            price_id = subscription["items"]["data"][0]["price"]["id"]
            tier = _tier_from_price_id(price_id, settings)
    except Exception as exc:
        logger.warning(f"Could not retrieve subscription price, defaulting to starter: {exc}")

    plaintext_key = _generate_api_key()
    key_hash = _hash_api_key(plaintext_key)
    now = datetime.now(timezone.utc)

    new_key = ApiKey(
        id=str(uuid.uuid4()),
        key_hash=key_hash,
        developer_id=user_id,
        name=f"{tier.capitalize()} API Key",
        tier=tier,
        is_active=True,
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=stripe_subscription_id,
        daily_request_count=0,
        daily_reset_at=now + timedelta(days=1),
        created_at=now,
    )
    db.add(new_key)
    await db.commit()

    # Store plaintext key for one-time display via Redis (10-min TTL)
    try:
        from app.cache import get_redis
        redis = await get_redis()
        await redis.setex(f"pending_api_key:{user_id}", 600, plaintext_key)
    except Exception as exc:
        logger.warning(f"Could not store pending key in Redis for user {user_id}: {exc}")

    logger.info(
        f"Provisioned {tier} API key for user={user_id} "
        f"customer={stripe_customer_id} subscription={stripe_subscription_id}"
    )


async def _handle_subscription_updated(subscription: dict, db: AsyncSession, settings) -> None:
    subscription_id = subscription.get("id")
    if not subscription_id:
        return

    try:
        price_id = subscription["items"]["data"][0]["price"]["id"]
        new_tier = _tier_from_price_id(price_id, settings)
    except (KeyError, IndexError, TypeError):
        logger.warning(f"Could not extract price from subscription.updated: {subscription_id}")
        return

    result = await db.execute(
        update(ApiKey)
        .where(ApiKey.stripe_subscription_id == subscription_id, ApiKey.is_active == True)
        .values(tier=new_tier)
        .returning(ApiKey.id)
    )
    updated = result.fetchall()
    await db.commit()
    logger.info(
        f"subscription.updated: set tier={new_tier} for {len(updated)} key(s) "
        f"subscription={subscription_id}"
    )


async def _handle_subscription_deleted(subscription: dict, db: AsyncSession, settings) -> None:
    subscription_id = subscription.get("id")
    if not subscription_id:
        return

    now = datetime.now(timezone.utc)

    # Revoke the existing paid key
    result = await db.execute(
        update(ApiKey)
        .where(ApiKey.stripe_subscription_id == subscription_id, ApiKey.is_active == True)
        .values(is_active=False, revoked_at=now)
        .returning(ApiKey.developer_id, ApiKey.id)
    )
    revoked_rows = result.fetchall()
    await db.commit()

    if not revoked_rows:
        logger.warning(f"subscription.deleted: no active key found for subscription={subscription_id}")
        return

    # Provision a free-tier key for each affected developer
    for developer_id, _ in revoked_rows:
        plaintext_key = _generate_api_key()
        free_key = ApiKey(
            id=str(uuid.uuid4()),
            key_hash=_hash_api_key(plaintext_key),
            developer_id=developer_id,
            name="Free API Key",
            tier="free",
            is_active=True,
            daily_request_count=0,
            daily_reset_at=now + timedelta(days=1),
            created_at=now,
        )
        db.add(free_key)

        try:
            from app.cache import get_redis
            redis = await get_redis()
            await redis.setex(f"pending_api_key:{developer_id}", 600, plaintext_key)
        except Exception as exc:
            logger.warning(f"Could not store free key in Redis for user {developer_id}: {exc}")

    await db.commit()
    logger.info(
        f"subscription.deleted: revoked {len(revoked_rows)} key(s) and provisioned free keys "
        f"subscription={subscription_id}"
    )


def _handle_payment_failed(invoice: dict) -> None:
    customer_id = invoice.get("customer")
    invoice_id = invoice.get("id")
    amount_due = invoice.get("amount_due", 0)
    logger.warning(
        f"invoice.payment_failed: customer={customer_id} invoice={invoice_id} "
        f"amount_due={amount_due} (grace period handling in Phase 2)"
    )
