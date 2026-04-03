"""Unit tests for affiliate_links module."""

import importlib
import sys
from unittest.mock import patch

import pytest

def _reload_module(env_overrides: dict):
    """Reload affiliate_links with specific env vars patched in."""
    with patch.dict("os.environ", env_overrides, clear=False):
        if "app.affiliate_links" in sys.modules:
            del sys.modules["app.affiliate_links"]
        import app.affiliate_links as m
        importlib.reload(m)
    return m


class TestUrlValidation:
    def setup_method(self):
        self.m = _reload_module({})

    def test_valid_https_url(self):
        assert self.m.is_valid_url("https://shopee.sg/product/12345") is True

    def test_valid_http_url(self):
        assert self.m.is_valid_url("http://example.com/product") is True

    def test_valid_url_with_port(self):
        assert self.m.is_valid_url("https://localhost:8080/product") is True

    def test_invalid_empty_string(self):
        assert self.m.is_valid_url("") is False

    def test_invalid_none(self):
        assert self.m.is_valid_url(None) is False

    def test_invalid_no_scheme(self):
        assert self.m.is_valid_url("shopee.sg/product/12345") is False

    def test_invalid_missing_domain(self):
        assert self.m.is_valid_url("https://") is False

    def test_invalid_random_string(self):
        assert self.m.is_valid_url("not-a-url-at-all") is False


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

    def test_rejects_invalid_url(self):
        result = self.m.get_affiliate_url("shopee_sg", "not-a-valid-url")
        assert result == "not-a-valid-url"


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


class TestTrackingIdGeneration:
    def setup_method(self):
        self.m = _reload_module({})

    def test_generates_tracking_id_with_product_id(self):
        tracking_id = self.m._generate_tracking_id(123, "shopee_sg")
        assert tracking_id.startswith("123_")
        assert len(tracking_id) > 5

    def test_different_ids_produce_different_tracking_ids(self):
        id1 = self.m._generate_tracking_id(123, "shopee_sg")
        id2 = self.m._generate_tracking_id(456, "shopee_sg")
        assert id1 != id2

    def test_same_id_produces_different_tracking_ids_over_time(self):
        import time
        id1 = self.m._generate_tracking_id(123, "shopee_sg")
        time.sleep(0.001)
        id2 = self.m._generate_tracking_id(123, "shopee_sg")
        assert id1 != id2


class TestParseTrackingId:
    def setup_method(self):
        self.m = _reload_module({})

    def test_parse_valid_tracking_id(self):
        tracking_id = self.m._generate_tracking_id(123, "shopee_sg")
        result = self.m.parse_tracking_id(tracking_id)
        assert result is not None
        product_id, suffix = result
        assert product_id == 123
        assert len(suffix) > 0

    def test_parse_invalid_format_no_underscore(self):
        result = self.m.parse_tracking_id("123abc")
        assert result is None

    def test_parse_invalid_non_numeric_product_id(self):
        result = self.m.parse_tracking_id("abc_def")
        assert result is None

    def test_parse_invalid_empty(self):
        result = self.m.parse_tracking_id("")
        assert result is None


class TestClickTrackingUrlGeneration:
    def setup_method(self):
        self.m = _reload_module({
            "SHOPEE_AFFILIATE_ID": "",
            "LAZADA_TRACKING_ID": "",
            "TRACKING_BASE_URL": "https://api.buywhere.ai"
        })

    def test_wraps_with_tracking_url_when_product_id_provided(self):
        url = "https://shopee.sg/product/12345"
        result = self.m.get_affiliate_url("shopee_sg", url, product_id=42)
        assert result.startswith("https://api.buywhere.ai/v1/track/")

    def test_no_tracking_wrapper_without_product_id(self):
        url = "https://shopee.sg/product/12345"
        result = self.m.get_affiliate_url("shopee_sg", url)
        assert result == f"{url}?ref=buywhere"

    def test_no_tracking_wrapper_without_tracking_base_url(self):
        m = _reload_module({
            "SHOPEE_AFFILIATE_ID": "",
            "LAZADA_TRACKING_ID": "",
            "TRACKING_BASE_URL": ""
        })
        url = "https://shopee.sg/product/12345"
        result = m.get_affiliate_url("shopee_sg", url, product_id=42)
        assert result == f"{url}?ref=buywhere"


class TestUnderlyingAffiliateUrl:
    def setup_method(self):
        self.m = _reload_module({
            "SHOPEE_AFFILIATE_ID": "",
            "LAZADA_TRACKING_ID": "",
            "TRACKING_BASE_URL": "https://api.buywhere.ai"
        })

    def test_returns_raw_affiliate_url_without_tracking(self):
        url = "https://shopee.sg/product/12345"
        result = self.m.get_underlying_affiliate_url("shopee_sg", url)
        assert "ref=buywhere" in result
        assert "api.buywhere.ai" not in result