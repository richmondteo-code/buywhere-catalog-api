"""
BuyWhere Affiliate Link Wrapper
===============================
Converts raw product URLs (Shopee SG, Lazada SG) into tracked affiliate links.

Production credentials (optional — graceful fallback if absent):
  Shopee:  SHOPEE_AFFILIATE_ID  — your Shopee Affiliate Portal publisher ID
  Lazada:  LAZADA_TRACKING_ID   — your Lazada Affiliate / Involve Asia tracking ID

Without credentials the module appends lightweight UTM / ref params so we can
at least measure referral traffic while full affiliate integration is pending.

Click Tracking:
  When TRACKING_BASE_URL is set, affiliate URLs are wrapped through a click
  tracking endpoint that records clicks before redirecting to the destination.
"""

import os
import re
from urllib.parse import quote

TRACKING_BASE_URL = os.environ.get("TRACKING_BASE_URL", "").rstrip("/")

_URL_PATTERN = re.compile(
    r"^https?://"
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
    r"localhost|"
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    r"(?::\d+)?"
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


def is_valid_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    return bool(_URL_PATTERN.match(url))


def _shopee_affiliate_url(product_url: str) -> str:
    shopee_affiliate_id = os.environ.get("SHOPEE_AFFILIATE_ID", "")
    if shopee_affiliate_id:
        encoded = quote(product_url, safe="")
        return f"https://shope.ee/api/v2/deep_link?affiliate_id={shopee_affiliate_id}&url={encoded}"
    sep = "&" if "?" in product_url else "?"
    return f"{product_url}{sep}ref=buywhere"


def _lazada_affiliate_url(product_url: str) -> str:
    lazada_tracking_id = os.environ.get("LAZADA_TRACKING_ID", "")
    if lazada_tracking_id:
        encoded = quote(product_url, safe="")
        return f"https://invol.co/cl{lazada_tracking_id}?p={encoded}"
    utm = "utm_source=buywhere&utm_medium=affiliate&utm_campaign=catalog"
    sep = "&" if "?" in product_url else "?"
    return f"{product_url}{sep}{utm}"


_PLATFORM_HANDLERS = {
    "shopee_sg": _shopee_affiliate_url,
    "lazada_sg": _lazada_affiliate_url,
}


def get_affiliate_url(platform: str, product_url: str, product_id: int | None = None) -> str:
    """Return a tracked affiliate URL for the given product.

    Args:
        platform:    Source platform identifier, e.g. ``"shopee_sg"`` or
                     ``"lazada_sg"``.
        product_url: The raw product URL from the catalog.
        product_id:  Optional product ID for click tracking.

    Returns:
        A tracked affiliate URL.  If the platform is unrecognised or the
        original URL is falsy/invalid, the original URL is returned unchanged.
    """
    if not product_url or not is_valid_url(product_url):
        return product_url

    handler = _PLATFORM_HANDLERS.get(platform)
    if handler is None:
        return product_url

    affiliate_url = handler(product_url)

    if TRACKING_BASE_URL and product_id:
        tracking_id = _generate_tracking_id(product_id, platform)
        return f"{TRACKING_BASE_URL}/v1/track/{tracking_id}"

    return affiliate_url


def get_underlying_affiliate_url(platform: str, product_url: str) -> str:
    """Return the raw affiliate URL without tracking wrapper (for click recording)."""
    if not product_url or not is_valid_url(product_url):
        return product_url

    handler = _PLATFORM_HANDLERS.get(platform)
    if handler is None:
        return product_url

    return handler(product_url)


def _generate_tracking_id(product_id: int, platform: str) -> str:
    import base64
    import hashlib
    import time
    raw = f"{product_id}:{platform}:{time.time_ns()}"
    digest = base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest()[:12]).decode().rstrip("=")
    return f"{product_id}_{digest}"


def parse_tracking_id(tracking_id: str) -> tuple[int, str] | None:
    try:
        parts = tracking_id.split("_", 1)
        if len(parts) != 2:
            return None
        product_id = int(parts[0])
        return (product_id, parts[1])
    except (ValueError, IndexError):
        return None