"""Pytest fixtures for catalog API tests."""

import sys
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, "/home/paperclip/buywhere-api")

from app.models.product import ApiKey, Product, IngestionRun


@pytest.fixture
def mock_api_key():
    key = MagicMock(spec=ApiKey)
    key.id = "test-key-id"
    key.key_hash = "test-hash"
    key.developer_id = "test-developer"
    key.name = "Test Key"
    key.tier = "basic"
    key.is_active = True
    return key


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def sample_product():
    p = MagicMock(spec=Product)
    p.id = 1
    p.sku = "SKU-001"
    p.source = "shopee_sg"
    p.merchant_id = "merchant_001"
    p.title = "iPhone 14 Pro Max 256GB"
    p.description = "Brand new iPhone"
    p.price = Decimal("1999.00")
    p.currency = "SGD"
    p.url = "https://shopee.sg/product/123"
    p.brand = "Apple"
    p.category = "Electronics"
    p.category_path = ["Electronics", "Phones", "Mobile Phones"]
    p.image_url = "https://shopee.sg/image.jpg"
    p.rating = Decimal("4.5")
    p.is_active = True
    p.metadata_ = {"original_price": Decimal("2499.00"), "condition": "new"}
    p.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    p.updated_at = datetime(2024, 1, 15, tzinfo=timezone.utc)
    return p


@pytest.fixture
def sample_products(sample_product):
    p1 = MagicMock(spec=Product)
    p1.id = 1
    p1.sku = "SKU-001"
    p1.source = "shopee_sg"
    p1.merchant_id = "merchant_001"
    p1.title = "iPhone 14 Pro Max 256GB"
    p1.description = "Brand new iPhone"
    p1.price = Decimal("1999.00")
    p1.currency = "SGD"
    p1.url = "https://shopee.sg/product/123"
    p1.brand = "Apple"
    p1.category = "Electronics"
    p1.category_path = ["Electronics", "Phones"]
    p1.image_url = "https://shopee.sg/image.jpg"
    p1.is_active = True
    p1.metadata_ = {"original_price": Decimal("2499.00")}
    p1.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    p1.updated_at = datetime(2024, 1, 15, tzinfo=timezone.utc)

    p2 = MagicMock(spec=Product)
    p2.id = 2
    p2.sku = "SKU-002"
    p2.source = "lazada_sg"
    p2.merchant_id = "merchant_002"
    p2.title = "Samsung Galaxy S23"
    p2.description = "Samsung flagship phone"
    p2.price = Decimal("1299.00")
    p2.currency = "SGD"
    p2.url = "https://lazada.sg/product/456"
    p2.brand = "Samsung"
    p2.category = "Electronics"
    p2.category_path = ["Electronics", "Phones"]
    p2.image_url = "https://lazada.sg/image.jpg"
    p2.is_active = True
    p2.metadata_ = {"original_price": Decimal("1599.00")}
    p2.created_at = datetime(2024, 1, 2, tzinfo=timezone.utc)
    p2.updated_at = datetime(2024, 1, 16, tzinfo=timezone.utc)

    p3 = MagicMock(spec=Product)
    p3.id = 3
    p3.sku = "SKU-003"
    p3.source = "carousell"
    p3.merchant_id = "merchant_carousell"
    p3.title = "Nike Air Max"
    p3.description = "Running shoes"
    p3.price = Decimal("150.00")
    p3.currency = "SGD"
    p3.url = "https://carousell.com/product/789"
    p3.brand = "Nike"
    p3.category = "Fashion"
    p3.category_path = ["Fashion", "Shoes"]
    p3.image_url = "https://carousell.com/image.jpg"
    p3.is_active = True
    p3.metadata_ = {"original_price": Decimal("200.00")}
    p3.created_at = datetime(2024, 1, 3, tzinfo=timezone.utc)
    p3.updated_at = datetime(2024, 1, 17, tzinfo=timezone.utc)

    return [p1, p2, p3]


@pytest.fixture
def sample_ingestion_run():
    run = MagicMock(spec=IngestionRun)
    run.id = 1
    run.source = "shopee_sg"
    run.started_at = datetime(2024, 1, 15, tzinfo=timezone.utc)
    run.finished_at = datetime(2024, 1, 15, 1, tzinfo=timezone.utc)
    run.rows_inserted = 100
    run.rows_updated = 50
    run.rows_failed = 5
    run.status = "completed"
    run.error_message = None
    return run


@pytest.fixture
def mock_request():
    from starlette.requests import Request
    request = MagicMock(spec=Request)
    request.state = MagicMock()
    return request


@pytest.fixture(autouse=True)
def mock_limiter():
    with patch("app.routers.products.limiter.limit", lambda *args, **kwargs: lambda f: f), \
         patch("app.routers.search.limiter.limit", lambda *args, **kwargs: lambda f: f), \
         patch("app.routers.categories.limiter.limit", lambda *args, **kwargs: lambda f: f), \
         patch("app.routers.deals.limiter.limit", lambda *args, **kwargs: lambda f: f), \
         patch("app.routers.status.limiter.limit", lambda *args, **kwargs: lambda f: f):
        yield


@pytest.fixture
def mock_cache():
    with patch("app.cache.cache_get", new_callable=AsyncMock) as mock_get, \
         patch("app.cache.cache_set", new_callable=AsyncMock) as mock_set, \
         patch("app.cache.build_cache_key", side_effect=lambda *args, **kwargs: f"cache_key:{args}"):
        yield {"get": mock_get, "set": mock_set}


@pytest.fixture
def mock_affiliate_links():
    with patch("app.affiliate_links.get_affiliate_url", side_effect=lambda source, url: f"{url}?ref=buywhere"):
        yield
