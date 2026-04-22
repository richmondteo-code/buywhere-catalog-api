#!/usr/bin/env python3
"""
BUY-3682 fallback: create estimated Lazada/Shopee price coverage.

This script is intentionally gated. The task says synthetic prices are a
fallback only if live scraping cannot meet the 2026-04-24 06:00 UTC deadline.
By default it performs a dry run and refuses writes before that cutoff.

Usage:
    python scripts/stub_buy3682_synthetic_prices.py
    python scripts/stub_buy3682_synthetic_prices.py --no-dry-run
    python scripts/stub_buy3682_synthetic_prices.py --no-dry-run --force
"""

import argparse
import asyncio
import hashlib
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings


ISSUE_ID = "BUY-3682"
PARENT_ISSUE_ID = "BUY-3672"
FALLBACK_AFTER = datetime(2026, 4, 24, 6, 0, tzinfo=UTC)
TARGET_SOURCES = ("lazada_sg", "shopee_sg")


@dataclass(frozen=True)
class SyntheticTarget:
    slug: str
    title: str
    brand: str
    category: str
    price_sgd: Decimal
    match_terms: tuple[str, ...]


TARGETS = (
    SyntheticTarget(
        slug="iphone-16-pro-256gb-black-titanium",
        title="iPhone 16 Pro 256GB Black Titanium",
        brand="Apple",
        category="electronics/smartphones",
        price_sgd=Decimal("1599.00"),
        match_terms=("iphone", "16", "pro", "256", "black"),
    ),
    SyntheticTarget(
        slug="iphone-16-pro-256gb-white-titanium",
        title="iPhone 16 Pro 256GB White Titanium",
        brand="Apple",
        category="electronics/smartphones",
        price_sgd=Decimal("1599.00"),
        match_terms=("iphone", "16", "pro", "256", "white"),
    ),
    SyntheticTarget(
        slug="iphone-16-pro-256gb-natural-titanium",
        title="iPhone 16 Pro 256GB Natural Titanium",
        brand="Apple",
        category="electronics/smartphones",
        price_sgd=Decimal("1599.00"),
        match_terms=("iphone", "16", "pro", "256", "natural"),
    ),
    SyntheticTarget(
        slug="iphone-16-pro-256gb-desert-titanium",
        title="iPhone 16 Pro 256GB Desert Titanium",
        brand="Apple",
        category="electronics/smartphones",
        price_sgd=Decimal("1599.00"),
        match_terms=("iphone", "16", "pro", "256", "desert"),
    ),
    SyntheticTarget(
        slug="galaxy-s25-ultra-256gb",
        title="Samsung Galaxy S25 Ultra 256GB",
        brand="Samsung",
        category="electronics/smartphones",
        price_sgd=Decimal("1649.00"),
        match_terms=("galaxy", "s25", "ultra", "256"),
    ),
    SyntheticTarget(
        slug="airpods-pro-2-usb-c",
        title="AirPods Pro 2nd Gen USB-C",
        brand="Apple",
        category="electronics/audio",
        price_sgd=Decimal("349.00"),
        match_terms=("airpods", "pro", "2"),
    ),
    SyntheticTarget(
        slug="nintendo-switch-2-console",
        title="Nintendo Switch 2 Console",
        brand="Nintendo",
        category="electronics/gaming",
        price_sgd=Decimal("699.00"),
        match_terms=("nintendo", "switch", "2"),
    ),
)


def database_url() -> str:
    url = get_settings().database_url
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def stable_sku(source: str, target: SyntheticTarget) -> str:
    return f"{ISSUE_ID.lower()}-{source}-{target.slug}"


def retailer_search_url(source: str, title: str) -> str:
    query = quote_plus(title)
    if source == "lazada_sg":
        return f"https://www.lazada.sg/catalog/?q={query}"
    if source == "shopee_sg":
        return f"https://shopee.sg/search?keyword={query}"
    raise ValueError(f"Unsupported source: {source}")


def estimated_metadata(source: str, target: SyntheticTarget, now: datetime) -> dict[str, Any]:
    return {
        "estimated": True,
        "synthetic_price_stub": True,
        "issue_id": ISSUE_ID,
        "parent_issue_id": PARENT_ISSUE_ID,
        "source": source,
        "reason": "Fallback synthetic price coverage for electronics compare-page retailer threshold",
        "fallback_after": FALLBACK_AFTER.isoformat(),
        "generated_at": now.isoformat(),
        "estimate_method": "static SKU-level fallback price, replace with scraped retailer price when available",
        "target_slug": target.slug,
    }


def title_match_clause(alias: str, terms: tuple[str, ...]) -> str:
    return " AND ".join(f"lower({alias}.title) LIKE :term_{idx}" for idx, _ in enumerate(terms))


async def find_product_id(db: AsyncSession, source: str, target: SyntheticTarget) -> int | None:
    params = {"source": source}
    for idx, term in enumerate(target.match_terms):
        params[f"term_{idx}"] = f"%{term.lower()}%"

    query = text(
        f"""
        SELECT id
        FROM products p
        WHERE p.source = :source
          AND p.is_active = true
          AND {title_match_clause("p", target.match_terms)}
        ORDER BY p.updated_at DESC NULLS LAST, p.id DESC
        LIMIT 1
        """
    )
    result = await db.execute(query, params)
    row = result.first()
    return int(row.id) if row else None


async def ensure_product(
    db: AsyncSession,
    source: str,
    target: SyntheticTarget,
    now: datetime,
    dry_run: bool,
) -> tuple[int | None, str]:
    existing_id = await find_product_id(db, source, target)
    metadata = estimated_metadata(source, target, now)

    if existing_id is not None:
        if not dry_run:
            await db.execute(
                text(
                    """
                    UPDATE products
                    SET metadata = COALESCE(metadata, '{}'::jsonb) || CAST(:metadata AS jsonb),
                        data_updated_at = :now,
                        updated_at = :now
                    WHERE id = :product_id
                    """
                ),
                {"product_id": existing_id, "metadata": json_dumps(metadata), "now": now},
            )
        return existing_id, "matched"

    sku = stable_sku(source, target)
    product_id = synthetic_product_id(source, target)
    if not dry_run:
        await db.execute(
            text(
                """
                INSERT INTO products (
                    id, sku, source, merchant_id, title, description, price, currency, price_sgd,
                    region, country_code, url, brand, category, category_path, image_url,
                    is_active, is_available, in_stock, stock_level, last_checked,
                    data_updated_at, metadata, created_at, updated_at
                )
                VALUES (
                    :id, :sku, :source, :merchant_id, :title, :description, :price, 'SGD', :price,
                    'sg', 'SG', :url, :brand, :category, :category_path, '',
                    true, true, true, 'in_stock', :now,
                    :now, CAST(:metadata AS jsonb), :now, :now
                )
                ON CONFLICT (sku, source) DO UPDATE SET
                    price = EXCLUDED.price,
                    price_sgd = EXCLUDED.price_sgd,
                    is_active = true,
                    is_available = true,
                    in_stock = true,
                    stock_level = 'in_stock',
                    last_checked = EXCLUDED.last_checked,
                    data_updated_at = EXCLUDED.data_updated_at,
                    metadata = COALESCE(products.metadata, '{}'::jsonb) || EXCLUDED.metadata,
                    updated_at = EXCLUDED.updated_at
                RETURNING id
                """
            ),
            {
                "id": product_id,
                "sku": sku,
                "source": source,
                "merchant_id": source,
                "title": target.title,
                "description": f"Estimated fallback listing for {target.title}",
                "price": target.price_sgd,
                "url": retailer_search_url(source, target.title),
                "brand": target.brand,
                "category": target.category,
                "category_path": [target.category],
                "metadata": json_dumps(metadata),
                "now": now,
            },
        )
    return product_id, "created"


def synthetic_product_id(source: str, target: SyntheticTarget) -> int:
    digest = hashlib.sha256(stable_sku(source, target).encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def json_dumps(value: dict[str, Any]) -> str:
    import json

    return json.dumps(value, sort_keys=True, separators=(",", ":"))


async def price_history_exists(db: AsyncSession, product_id: int, source: str) -> bool:
    result = await db.execute(
        text(
            """
            SELECT 1
            FROM price_history
            WHERE product_id = :product_id
              AND source = :source
              AND recorded_at >= :fallback_after
            LIMIT 1
            """
        ),
        {"product_id": product_id, "source": source, "fallback_after": FALLBACK_AFTER},
    )
    return result.first() is not None


async def insert_price_history(
    db: AsyncSession,
    product_id: int,
    source: str,
    price: Decimal,
    now: datetime,
    dry_run: bool,
) -> bool:
    if await price_history_exists(db, product_id, source):
        return False
    if not dry_run:
        await db.execute(
            text(
                """
                INSERT INTO price_history (product_id, price, currency, source, recorded_at)
                VALUES (:product_id, :price, 'SGD', :source, :recorded_at)
                """
            ),
            {
                "product_id": product_id,
                "price": price,
                "source": source,
                "recorded_at": now,
            },
        )
    return True


async def run(dry_run: bool, force: bool, now: datetime) -> dict[str, int]:
    if should_refuse_write(dry_run=dry_run, force=force, now=now):
        raise SystemExit(
            f"Refusing writes before {FALLBACK_AFTER.isoformat()}; use --force only with explicit approval."
        )

    engine = create_async_engine(database_url(), echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    stats = {"matched": 0, "created": 0, "history_inserted": 0, "history_skipped": 0}

    async with session_factory() as db:
        for target in TARGETS:
            for source in TARGET_SOURCES:
                product_id, action = await ensure_product(db, source, target, now, dry_run)
                stats[action] += 1
                if product_id is None:
                    continue
                inserted = await insert_price_history(db, product_id, source, target.price_sgd, now, dry_run)
                if inserted:
                    stats["history_inserted"] += 1
                else:
                    stats["history_skipped"] += 1

        if dry_run:
            await db.rollback()
        else:
            await db.commit()

    await engine.dispose()
    return stats


def should_refuse_write(dry_run: bool, force: bool, now: datetime) -> bool:
    return not dry_run and not force and now < FALLBACK_AFTER


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BUY-3682 synthetic price fallback")
    parser.add_argument("--no-dry-run", action="store_true", help="Write product metadata and price_history rows")
    parser.add_argument("--force", action="store_true", help="Allow writes before the fallback deadline")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    dry_run = not args.no_dry_run
    now = datetime.now(UTC)
    stats = await run(dry_run=dry_run, force=args.force, now=now)
    mode = "dry-run" if dry_run else "write"
    print(f"{ISSUE_ID} synthetic price fallback {mode}: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
