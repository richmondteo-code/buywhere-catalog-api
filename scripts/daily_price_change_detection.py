#!/usr/bin/env python3
"""
Daily price change detection.

Compares current prices against yesterday's PriceHistory snapshots,
flags products with >5% change (up or down), stores PriceChangeEvent records,
and dispatches webhooks to registered developers.

Usage:
    python scripts/daily_price_change_detection.py --once
    python scripts/daily_price_change_detection.py --continuous

Cron example (daily at 3 AM UTC):
    0 3 * * * cd /home/paperclip/buywhere-api && python scripts/daily_price_change_detection.py --once
"""

import argparse
import asyncio
import fcntl
import logging
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, Base
from app.models.product import Product, PriceHistory, PriceChangeEvent
from app.services.webhook import dispatch_price_change_webhooks
from app.logging_centralized import get_logger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = get_logger("daily_price_change_detection")

LOCK_DIR = Path("/tmp/buywhere_price_change_detection_locks")
LOCK_DIR.mkdir(exist_ok=True)
LOCK_PATH = LOCK_DIR / "price_change_detection.lock"

PRICE_CHANGE_THRESHOLD_PCT = 5.0
BATCH_SIZE = 500


def acquire_lock(lock_path: Path):
    lock_file = open(lock_path, "w")
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_file.write(str(os.getpid()))
        lock_file.flush()
        return lock_file
    except (IOError, OSError):
        lock_file.close()
        return None


def release_lock(lock_file) -> None:
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()
    except Exception:
        pass


async def detect_price_changes(db: AsyncSession, batch_size: int = BATCH_SIZE) -> dict:
    """
    Compare current product prices against the most recent PriceHistory snapshot.
    Products with >5% price change are stored as PriceChangeEvent records and
    webhook notifications are dispatched.
    """
    products_checked = 0
    price_changes_detected = 0
    webhooks_dispatched = 0
    errors = []

    cutoff = datetime.now(timezone.utc) - timedelta(days=1)

    offset = 0
    while True:
        result = await db.execute(
            select(Product.id, Product.price, Product.currency, Product.source, Product.merchant_id)
            .where(Product.is_active == True)
            .offset(offset)
            .limit(batch_size)
        )
        products = result.all()
        if not products:
            break

        for product_id, current_price, currency, source, merchant_id in products:
            try:
                current_price_dec = Decimal(str(current_price)) if current_price else None
                if current_price_dec is None:
                    continue

                last_snapshot = await db.execute(
                    select(PriceHistory)
                    .where(
                        PriceHistory.product_id == product_id,
                        PriceHistory.recorded_at < cutoff,
                    )
                    .order_by(desc(PriceHistory.recorded_at))
                    .limit(1)
                )
                snapshot = last_snapshot.scalar_one_or_none()
                if not snapshot:
                    continue

                products_checked += 1

                old_price_dec = Decimal(str(snapshot.price))
                if old_price_dec <= 0:
                    continue

                change_pct = round(float((current_price_dec - old_price_dec) / old_price_dec) * 100, 2)

                if abs(change_pct) < PRICE_CHANGE_THRESHOLD_PCT:
                    continue

                direction = "increase" if change_pct > 0 else "decrease"

                event = PriceChangeEvent(
                    product_id=product_id,
                    old_price=old_price_dec,
                    new_price=current_price_dec,
                    change_pct=Decimal(str(change_pct)),
                    direction=direction,
                    currency=currency or "SGD",
                    source=source,
                    merchant_id=merchant_id,
                )
                db.add(event)
                price_changes_detected += 1

                product_result = await db.execute(
                    select(Product).where(Product.id == product_id)
                )
                product = product_result.scalar_one_or_none()
                if product:
                    product_dict = {
                        "id": product.id,
                        "title": product.title,
                        "price": float(current_price_dec),
                        "currency": currency or "SGD",
                        "source": product.source,
                        "merchant_id": product.merchant_id,
                        "url": product.url,
                        "image_url": product.image_url,
                        "brand": product.brand,
                        "category": product.category,
                    }
                    try:
                        delivered = await dispatch_price_change_webhooks(
                            db, product_dict, old_price_dec, current_price_dec
                        )
                        webhooks_dispatched += len(delivered)
                    except Exception as e:
                        logger.warning(f"Webhook dispatch error for product {product_id}: {e}")

            except Exception as e:
                logger.exception(f"Error processing product {product_id}: {e}")
                errors.append({"product_id": int(product_id), "error": str(e)})

        await db.commit()
        offset += batch_size
        if len(products) < batch_size:
            break

    logger.info(
        f"Price change detection completed: "
        f"products_checked={products_checked}, "
        f"price_changes_detected={price_changes_detected}, "
        f"webhooks_dispatched={webhooks_dispatched}, "
        f"errors={len(errors)}"
    )

    return {
        "products_checked": products_checked,
        "price_changes_detected": price_changes_detected,
        "webhooks_dispatched": webhooks_dispatched,
        "errors": errors,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }


async def run_detection_cycle(batch_size: int) -> dict:
    lock_file = acquire_lock(LOCK_PATH)
    if lock_file is None:
        logger.warning("Could not acquire lock, another detection run may be active")
        return {"error": "Could not acquire lock"}

    try:
        logger.info(f"Price change detection started at {datetime.now(timezone.utc)}")
        stats = await detect_price_changes(AsyncSessionLocal(), batch_size=batch_size)
        logger.info(f"Price change detection finished at {datetime.now(timezone.utc)}")
        return stats
    finally:
        release_lock(lock_file)


def run_once(batch_size: int = BATCH_SIZE) -> int:
    stats = asyncio.run(run_detection_cycle(batch_size=batch_size))
    if "error" in stats:
        return 0
    if stats["errors"]:
        return 1
    return 0


def run_continuous(interval_hours: int, batch_size: int = BATCH_SIZE) -> None:
    logger.info(
        f"Starting continuous price change detection (interval={interval_hours}h, batch_size={batch_size})"
    )
    while True:
        try:
            run_once(batch_size=batch_size)
        except KeyboardInterrupt:
            logger.info("Received interrupt, shutting down")
            break
        except Exception as exc:
            logger.exception(f"Error in price change detection: {exc}")
        time.sleep(interval_hours * 3600)


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily price change detection")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    parser.add_argument(
        "--interval-hours", type=int, default=24,
        help="Continuous mode interval in hours (default: 24)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=BATCH_SIZE,
        help=f"Maximum products to scan per run (default: {BATCH_SIZE})"
    )
    args = parser.parse_args()

    if args.once:
        raise SystemExit(run_once(batch_size=args.batch_size))
    if args.continuous:
        run_continuous(interval_hours=args.interval_hours, batch_size=args.batch_size)
        return

    parser.print_help()
    raise SystemExit(1)


if __name__ == "__main__":
    main()
