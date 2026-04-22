from datetime import UTC, datetime, timedelta

from scripts.stub_buy3682_synthetic_prices import (
    FALLBACK_AFTER,
    TARGETS,
    estimated_metadata,
    retailer_search_url,
    should_refuse_write,
    stable_sku,
    synthetic_product_id,
)


def test_write_guard_allows_dry_run_before_cutoff():
    before_cutoff = FALLBACK_AFTER - timedelta(minutes=1)

    assert should_refuse_write(dry_run=True, force=False, now=before_cutoff) is False
    assert should_refuse_write(dry_run=False, force=False, now=before_cutoff) is True
    assert should_refuse_write(dry_run=False, force=True, now=before_cutoff) is False


def test_stable_sku_and_product_id_are_deterministic():
    target = TARGETS[0]

    assert stable_sku("lazada_sg", target) == "buy-3682-lazada_sg-iphone-16-pro-256gb-black-titanium"
    assert synthetic_product_id("lazada_sg", target) == synthetic_product_id("lazada_sg", target)
    assert synthetic_product_id("lazada_sg", target) != synthetic_product_id("shopee_sg", target)


def test_metadata_marks_estimated_and_links_issue():
    now = datetime(2026, 4, 24, 6, 1, tzinfo=UTC)
    metadata = estimated_metadata("shopee_sg", TARGETS[-1], now)

    assert metadata["estimated"] is True
    assert metadata["synthetic_price_stub"] is True
    assert metadata["issue_id"] == "BUY-3682"
    assert metadata["parent_issue_id"] == "BUY-3672"
    assert metadata["source"] == "shopee_sg"


def test_retailer_search_urls_are_source_specific():
    title = "AirPods Pro 2nd Gen USB-C"

    assert retailer_search_url("lazada_sg", title).startswith("https://www.lazada.sg/catalog/?q=")
    assert retailer_search_url("shopee_sg", title).startswith("https://shopee.sg/search?keyword=")
