"""
BuyWhere Affiliate Link Wrapper
================================
Converts raw product URLs (Shopee SG, Lazada SG) into tracked affiliate links.

Production credentials (optional — graceful fallback if absent):
  Shopee:  SHOPEE_AFFILIATE_ID  — your Shopee Affiliate Portal publisher ID
  Lazada:  LAZADA_TRACKING_ID   — your Lazada Affiliate / Involve Asia tracking ID

Without credentials the module appends lightweight UTM / ref params so we can
at least measure referral traffic while full affiliate integration is pending.
"""

import os
from urllib.parse import urlparse, urlencode, parse_qs, urljoin
from urllib.parse import urlunparse, ParseResult

# ---------------------------------------------------------------------------
# Shopee SG
# ---------------------------------------------------------------------------

SHOPEE_AFFILIATE_ID = os.environ.get("SHOPEE_AFFILIATE_ID", "")

# Shopee Open Platform deep-link base (used when affiliate ID is present)
# Format: https://shope.ee/api/v2/deep_link?affiliate_id=<ID>&url=<encoded-product-url>
# Without the ID we fall back to adding `&ref=buywhere` query param.
_SHOPEE_DEEP_LINK_BASE = "https://shope.ee/api/v2/deep_link"


def _shopee_affiliate_url(product_url: str) -> str:
    if SHOPEE_AFFILIATE_ID:
        from urllib.parse import quote
        encoded = quote(product_url, safe="")
        return f"{_SHOPEE_DEEP_LINK_BASE}?affiliate_id={SHOPEE_AFFILIATE_ID}&url={encoded}"

    # Fallback: append ref param
    sep = "&" if "?" in product_url else "?"
    return f"{product_url}{sep}ref=buywhere"


# ---------------------------------------------------------------------------
# Lazada SG
# ---------------------------------------------------------------------------

LAZADA_TRACKING_ID = os.environ.get("LAZADA_TRACKING_ID", "")

# Involve Asia / Lazada affiliate base
# Format: https://invol.co/cl<TRACKING_ID>?p=<encoded-product-url>
_LAZADA_INVOLVE_BASE = "https://invol.co/cl"


def _lazada_affiliate_url(product_url: str) -> str:
    if LAZADA_TRACKING_ID:
        from urllib.parse import quote
        encoded = quote(product_url, safe="")
        return f"{_LAZADA_INVOLVE_BASE}{LAZADA_TRACKING_ID}?p={encoded}"

    # Fallback: UTM params
    utm = "utm_source=buywhere&utm_medium=affiliate&utm_campaign=catalog"
    sep = "&" if "?" in product_url else "?"
    return f"{product_url}{sep}{utm}"


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

_PLATFORM_HANDLERS = {
    "shopee_sg": _shopee_affiliate_url,
    "lazada_sg": _lazada_affiliate_url,
}


def get_affiliate_url(platform: str, product_url: str) -> str:
    """Return a tracked affiliate URL for the given product.

    Args:
        platform:    Source platform identifier, e.g. ``"shopee_sg"`` or
                     ``"lazada_sg"``.
        product_url: The raw product URL from the catalog.

    Returns:
        A tracked affiliate URL.  If the platform is unrecognised or the
        original URL is falsy, the original URL is returned unchanged.
    """
    if not product_url:
        return product_url

    handler = _PLATFORM_HANDLERS.get(platform)
    if handler is None:
        # Unknown platform — return original to avoid breaking the response
        return product_url

    return handler(product_url)
