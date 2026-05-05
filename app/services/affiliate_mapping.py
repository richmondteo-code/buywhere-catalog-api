"""Auto-mapping service: match network product IDs to BuyWhere products by barcode/sku."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.affiliate import AffiliateProductMapping
from app.models.product import Product
from app.models.affiliate import AffiliateCommission

logger = logging.getLogger("buywhere_api")


async def auto_map_product(
    db: AsyncSession,
    network: str,
    network_product_id: str,
) -> Optional[int]:
    """Attempt to match a network product ID to a BuyWhere product.

    Resolution order:
      1. Check existing `affiliate_product_mappings` for (network, network_product_id)
      2. Try matching `network_product_id` against `Product.barcode`
      3. Try matching `network_product_id` against `Product.sku`
      4. Try matching `network_product_id` against `Product.id` (direct integer match as fallback)

    On match, inserts a new row into `affiliate_product_mappings` with confidence
    reflecting the match method. Returns the `buywhere_product_id` or None.
    """
    mapping = await db.execute(
        select(AffiliateProductMapping).where(
            AffiliateProductMapping.network == network,
            AffiliateProductMapping.network_product_id == network_product_id,
        )
    )
    existing = mapping.scalar_one_or_none()
    if existing:
        return existing.buywhere_product_id

    buywhere_product_id, confidence = await _resolve_product(db, network_product_id)

    if buywhere_product_id is not None:
        mapping = AffiliateProductMapping(
            network=network,
            network_product_id=network_product_id,
            buywhere_product_id=buywhere_product_id,
            confidence=confidence,
        )
        db.add(mapping)
        await db.flush()
        logger.info(
            "Auto-mapped network=%s network_product_id=%s -> buywhere_product_id=%s (confidence=%s)",
            network, network_product_id, buywhere_product_id, confidence,
        )

    return buywhere_product_id


async def _resolve_product(
    db: AsyncSession,
    network_product_id: str,
) -> tuple[Optional[int], str]:
    """Resolve a network_product_id to a BuyWhere product ID.

    Returns (product_id, confidence) where confidence is one of:
      'exact', 'barcode', 'sku', 'id_match', or (None, 'unmatched').
    """
    product = await db.execute(
        select(Product).where(Product.barcode == network_product_id).limit(1)
    )
    row = product.scalar_one_or_none()
    if row:
        return row.id, "barcode"

    product = await db.execute(
        select(Product).where(Product.sku == network_product_id).limit(1)
    )
    row = product.scalar_one_or_none()
    if row:
        return row.id, "sku"

    try:
        product_id = int(network_product_id)
    except (ValueError, TypeError):
        return None, "unmatched"

    product = await db.execute(
        select(Product).where(Product.id == product_id).limit(1)
    )
    row = product.scalar_one_or_none()
    if row:
        return row.id, "id_match"

    return None, "unmatched"


async def get_unmapped_commissions(
    db: AsyncSession,
    network: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AffiliateCommission]:
    """Get commissions where no product mapping exists."""
    query = select(AffiliateCommission).where(
        AffiliateCommission.buywhere_product_id.is_(None)
    )
    if network:
        query = query.where(AffiliateCommission.network == network)
    query = query.order_by(AffiliateCommission.earned_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    return list(result.scalars().all())


async def create_manual_mapping(
    db: AsyncSession,
    network: str,
    network_product_id: str,
    buywhere_product_id: int,
    confidence: str = "manual",
) -> AffiliateProductMapping:
    """Create or update a manual product mapping override."""
    existing = await db.execute(
        select(AffiliateProductMapping).where(
            AffiliateProductMapping.network == network,
            AffiliateProductMapping.network_product_id == network_product_id,
        )
    )
    row = existing.scalar_one_or_none()
    if row:
        row.buywhere_product_id = buywhere_product_id
        row.confidence = confidence
        await db.flush()
        await db.refresh(row)
        return row

    mapping = AffiliateProductMapping(
        network=network,
        network_product_id=network_product_id,
        buywhere_product_id=buywhere_product_id,
        confidence=confidence,
    )
    db.add(mapping)
    await db.flush()
    await db.refresh(mapping)
    return mapping
