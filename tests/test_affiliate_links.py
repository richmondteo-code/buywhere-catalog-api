"""Unit tests for affiliate_links module."""

import importlib
import sys
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reload_module(env_overrides: dict):
    """Reload affiliate_links with specific env vars patched in."""
    with patch.dict("os.environ", env_overrides, clear=False):
        if "app.affiliate_links" in sys.modules:
            del sys.modules["app.affiliate_links"]
        import app.affiliate_links as m
        importlib.reload(m)
    return m


# ---------------------------------------------------------------------------
# Shopee SG — no credentials (fallback)
# ---------------------------------------------------------------------------

class TestShopeeSGFallback:
    def setup_method(self):
        self.m = _reload_module({"SHOPEE_AFFILIATE_ID": "", "LAZADA_TRACKING_ID": ""})

    def test_appends_ref_param_no_existing_query(self):
        url = "https://shopee.sg/product/12345"
        result = self.m.get_affiliate_url("shopee_sg", url)
        assert result == f"{url}?ref=buywhere"

    def test_appends_ref_param_with_existing_query(self):
        url = "https://shopee.sg/product/12345?color=red"
        result = self.m.get_affiliate_url("shopee_sg", url)
        assert result == f"{url}&ref=buywhere"

    def test_returns_original_for_empty_url(self):
        result = self.m.get_affiliate_url("shopee_sg", "")
        assert result == ""


# ---------------------------------------------------------------------------
# Shopee SG — with credentials
# ---------------------------------------------------------------------------

class TestShopeeSGWithCredentials:
    AFFILIATE_ID = "testpub123"

    def setup_method(self):
        self.m = _reload_module({"SHOPEE_AFFILIATE_ID": self.AFFILIATE_ID, "LAZADA_TRACKING_ID": ""})

    def test_uses_deep_link_base(self):
        url = "https://shopee.sg/product/12345"
        result = self.m.get_affiliate_url("shopee_sg", url)
        assert result.startswith("https://shope.ee/api/v2/deep_link")
        assert f"affiliate_id={self.AFFILIATE_ID}" in result
        assert "url=" in result

    def test_product_url_is_encoded(self):
        url = "https://shopee.sg/product/12345?ref=abc&foo=bar"
        result = self.m.get_affiliate_url("shopee_sg", url)
        # Original URL should not appear literally (it's percent-encoded)
        assert url not in result
        assert "%3F" in result or "%26" in result  # ? or & encoded


# ---------------------------------------------------------------------------
# Lazada SG — no credentials (fallback)
# ---------------------------------------------------------------------------

class TestLazadaSGFallback:
    def setup_method(self):
        self.m = _reload_module({"SHOPEE_AFFILIATE_ID": "", "LAZADA_TRACKING_ID": ""})

    def test_appends_utm_params_no_existing_query(self):
        url = "https://www.lazada.sg/products/laptop-i123456.html"
        result = self.m.get_affiliate_url("lazada_sg", url)
        assert "utm_source=buywhere" in result
        assert "utm_medium=affiliate" in result
        assert "utm_campaign=catalog" in result
        assert result.startswith(url + "?")

    def test_appends_utm_params_with_existing_query(self):
        url = "https://www.lazada.sg/products/laptop-i123456.html?color=black"
        result = self.m.get_affiliate_url("lazada_sg", url)
        assert "utm_source=buywhere" in result
        assert result.startswith(url + "&")

    def test_returns_original_for_empty_url(self):
        result = self.m.get_affiliate_url("lazada_sg", "")
        assert result == ""


# ---------------------------------------------------------------------------
# Lazada SG — with credentials
# ---------------------------------------------------------------------------

class TestLazadaSGWithCredentials:
    TRACKING_ID = "abc999xyz"

    def setup_method(self):
        self.m = _reload_module({"LAZADA_TRACKING_ID": self.TRACKING_ID, "SHOPEE_AFFILIATE_ID": ""})

    def test_uses_involve_asia_base(self):
        url = "https://www.lazada.sg/products/laptop-i123456.html"
        result = self.m.get_affiliate_url("lazada_sg", url)
        assert result.startswith(f"https://invol.co/cl{self.TRACKING_ID}")
        assert "p=" in result

    def test_product_url_is_encoded(self):
        url = "https://www.lazada.sg/products/laptop-i123456.html?color=black"
        result = self.m.get_affiliate_url("lazada_sg", url)
        assert url not in result
        assert "%3A" in result  # : is encoded


# ---------------------------------------------------------------------------
# Unknown platform
# ---------------------------------------------------------------------------

class TestUnknownPlatform:
    def setup_method(self):
        self.m = _reload_module({})

    def test_returns_original_url_for_unknown_platform(self):
        url = "https://example.com/product/abc"
        result = self.m.get_affiliate_url("tokopedia_id", url)
        assert result == url

    def test_returns_empty_for_empty_url_unknown_platform(self):
        result = self.m.get_affiliate_url("unknown", "")
        assert result == ""
