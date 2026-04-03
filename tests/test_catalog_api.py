"""Comprehensive tests for catalog API endpoints."""

import asyncio
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from app.schemas.product import (
    ProductListResponse, ProductResponse, CompareResponse, CompareMatch,
    CategoryNode, CategoryResponse,
)
from app.schemas.status import CatalogStatus, PlatformProductCount, IngestionRunInfo
from app.routers.deals import DealItem, DealsResponse


class TestProductsRouter:
    """Tests for /v1/products endpoints."""

    def test_map_product(self, sample_product):
        from app.routers.products import _map_product
        result = _map_product(sample_product)

        assert isinstance(result, ProductResponse)
        assert result.id == sample_product.id
        assert result.sku == sample_product.sku
        assert result.source == sample_product.source
        assert result.name == sample_product.title
        assert result.price == sample_product.price
        assert result.currency == sample_product.currency
        assert result.availability == sample_product.is_active

    def test_search_products_cache_hit(self, mock_db, mock_api_key, mock_request, mock_cache):
        async def run_test():
            from app.routers.products import search_products

            cached_data = {
                "total": 1,
                "limit": 20,
                "offset": 0,
                "items": [{
                    "id": 1,
                    "sku": "SKU-001",
                    "source": "shopee_sg",
                    "merchant_id": "merchant_001",
                    "name": "Test Product",
                    "price": Decimal("99.99"),
                    "currency": "SGD",
                    "buy_url": "https://shopee.sg/product/1",
                    "availability": True,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }]
            }
            mock_cache["get"].return_value = cached_data

            result = await search_products(
                request=mock_request,
                q="test",
                category=None,
                min_price=None,
                max_price=None,
                source=None,
                limit=20,
                offset=0,
                db=mock_db,
                api_key=mock_api_key,
            )

            assert isinstance(result, ProductListResponse)
            assert result.total == 1
            mock_cache["get"].assert_called_once()

        asyncio.run(run_test())

    def test_search_products_cache_miss(self, mock_db, mock_api_key, mock_request, mock_cache, sample_products):
        async def run_test():
            from app.routers.products import search_products
            from app.schemas.product import ProductResponse

            mock_cache["get"].return_value = None

            def execute_side_effect(query):
                if "COUNT" in str(query):
                    mock_count = MagicMock()
                    mock_count.scalar_one.return_value = 2
                    return mock_count
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = sample_products[:2]
                return mock_result

            mock_db.execute.side_effect = execute_side_effect

            def map_product_mock(p):
                return ProductResponse(
                    id=p.id,
                    sku=p.sku,
                    source=p.source,
                    merchant_id=p.merchant_id,
                    name=p.title,
                    description=p.description,
                    price=p.price,
                    currency=p.currency,
                    buy_url=p.url,
                    affiliate_url=p.url + "?ref=buywhere" if p.url else None,
                    image_url=p.image_url,
                    category=p.category,
                    category_path=p.category_path,
                    availability=p.is_active,
                    metadata=p.metadata_,
                    updated_at=p.updated_at,
                )

            with patch("app.routers.products._map_product", side_effect=map_product_mock):
                result = await search_products(
                    request=mock_request,
                    q=None,
                    category="Electronics",
                    min_price=None,
                    max_price=None,
                    source=None,
                    limit=20,
                    offset=0,
                    db=mock_db,
                    api_key=mock_api_key,
                )

            assert isinstance(result, ProductListResponse)
            mock_cache["set"].assert_called_once()

        asyncio.run(run_test())

    def test_get_product_found(self, mock_db, mock_api_key, mock_request, mock_cache, sample_product):
        async def run_test():
            from app.routers.products import get_product

            mock_cache["get"].return_value = None
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = sample_product
            mock_db.execute.return_value = mock_result

            with patch("app.routers.products._map_product", return_value=MagicMock(id=sample_product.id)):
                result = await get_product(
                    request=mock_request,
                    product_id=1,
                    db=mock_db,
                    api_key=mock_api_key,
                )

            assert result is not None

        asyncio.run(run_test())

    def test_get_product_not_found(self, mock_db, mock_api_key, mock_request, mock_cache):
        async def run_test():
            from app.routers.products import get_product

            mock_cache["get"].return_value = None
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            with pytest.raises(HTTPException) as exc_info:
                await get_product(
                    request=mock_request,
                    product_id=999,
                    db=mock_db,
                    api_key=mock_api_key,
                )

            assert exc_info.value.status_code == 404

        asyncio.run(run_test())

    def test_best_price_found(self, mock_db, mock_api_key, mock_request, sample_product):
        async def run_test():
            from app.routers.products import best_price

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = sample_product
            mock_db.execute.return_value = mock_result

            with patch("app.routers.products._map_product", return_value=MagicMock(id=sample_product.id)):
                result = await best_price(
                    request=mock_request,
                    q="iPhone 14 Pro Max",
                    category=None,
                    db=mock_db,
                    api_key=mock_api_key,
                )

            assert result is not None

        asyncio.run(run_test())

    def test_best_price_not_found(self, mock_db, mock_api_key, mock_request):
        async def run_test():
            from app.routers.products import best_price

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.side_effect = [mock_result, mock_result]

            with pytest.raises(HTTPException) as exc_info:
                await best_price(
                    request=mock_request,
                    q="nonexistent product xyz123",
                    category=None,
                    db=mock_db,
                    api_key=mock_api_key,
                )

            assert exc_info.value.status_code == 404
            assert "No products found" in str(exc_info.value.detail)

        asyncio.run(run_test())

    def test_compare_product_not_found(self, mock_db, mock_api_key, mock_request, mock_cache):
        async def run_test():
            from app.routers.products import compare_product

            mock_cache["get"].return_value = None
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            with pytest.raises(HTTPException) as exc_info:
                await compare_product(
                    request=mock_request,
                    product_id=999,
                    min_price=None,
                    max_price=None,
                    db=mock_db,
                    api_key=mock_api_key,
                )

            assert exc_info.value.status_code == 404

        asyncio.run(run_test())


class TestSearchRouter:
    """Tests for /v1/search endpoint."""

    def test_search_cache_hit(self, mock_db, mock_api_key, mock_request, mock_cache):
        async def run_test():
            from app.routers.search import search_products

            cached_data = {
                "total": 1,
                "limit": 20,
                "offset": 0,
                "items": []
            }
            mock_cache["get"].return_value = cached_data

            result = await search_products(
                request=mock_request,
                q="test query",
                category=None,
                min_price=None,
                max_price=None,
                limit=20,
                offset=0,
                db=mock_db,
                api_key=mock_api_key,
            )

            assert isinstance(result, ProductListResponse)
            mock_db.execute.assert_not_called()

        asyncio.run(run_test())

    def test_search_cache_miss(self, mock_db, mock_api_key, mock_request, mock_cache, sample_products):
        async def run_test():
            from app.routers.search import search_products
            from app.schemas.product import ProductResponse

            mock_cache["get"].return_value = None

            def execute_side_effect(query):
                mock_result = MagicMock()
                if "COUNT" in str(query):
                    mock_result.scalar_one.return_value = 2
                else:
                    mock_result.scalars.return_value.all.return_value = sample_products[:2]
                return mock_result

            mock_db.execute.side_effect = execute_side_effect

            def map_product_mock(p):
                return ProductResponse(
                    id=p.id,
                    sku=p.sku,
                    source=p.source,
                    merchant_id=p.merchant_id,
                    name=p.title,
                    description=p.description,
                    price=p.price,
                    currency=p.currency,
                    buy_url=p.url,
                    affiliate_url=p.url + "?ref=buywhere" if p.url else None,
                    image_url=p.image_url,
                    category=p.category,
                    category_path=p.category_path,
                    availability=p.is_active,
                    metadata=p.metadata_,
                    updated_at=p.updated_at,
                )

            with patch("app.routers.search._map_product", side_effect=map_product_mock):
                result = await search_products(
                    request=mock_request,
                    q="iPhone",
                    category=None,
                    min_price=None,
                    max_price=None,
                    limit=20,
                    offset=0,
                    db=mock_db,
                    api_key=mock_api_key,
                )

            assert isinstance(result, ProductListResponse)
            mock_cache["set"].assert_called_once()

        asyncio.run(run_test())


class TestCategoriesRouter:
    """Tests for /v1/categories endpoint."""

    def test_list_categories(self, mock_db, mock_api_key, mock_request):
        async def run_test():
            from app.routers.categories import list_categories

            mock_result = MagicMock()
            mock_result.all.return_value = [
                MagicMock(category="Electronics", count=100),
                MagicMock(category="Fashion", count=50),
                MagicMock(category="Home & Living", count=75),
            ]
            mock_db.execute.return_value = mock_result

            result = await list_categories(
                request=mock_request,
                db=mock_db,
                api_key=mock_api_key,
            )

            assert isinstance(result, CategoryResponse)
            assert result.total == 3
            assert len(result.categories) == 3
            assert result.categories[0].name == "Electronics"
            assert result.categories[0].count == 100

        asyncio.run(run_test())

    def test_list_categories_empty(self, mock_db, mock_api_key, mock_request):
        async def run_test():
            from app.routers.categories import list_categories

            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_db.execute.return_value = mock_result

            result = await list_categories(
                request=mock_request,
                db=mock_db,
                api_key=mock_api_key,
            )

            assert isinstance(result, CategoryResponse)
            assert result.total == 0
            assert len(result.categories) == 0

        asyncio.run(run_test())


class TestDealsRouter:
    """Tests for /v1/deals endpoint."""

    def test_get_deals_default_params(self, mock_db, mock_api_key, mock_request, sample_products):
        async def run_test():
            from app.routers.deals import get_deals

            def execute_side_effect(query):
                mock_result = MagicMock()
                if "COUNT" in str(query):
                    mock_result.scalar_one.return_value = 2
                else:
                    mock_result.scalars.return_value.all.return_value = sample_products[:2]
                return mock_result

            mock_db.execute.side_effect = execute_side_effect

            result = await get_deals(
                request=mock_request,
                category=None,
                min_discount_pct=10.0,
                limit=20,
                offset=0,
                db=mock_db,
                api_key=mock_api_key,
            )

            assert isinstance(result, DealsResponse)
            assert result.limit == 20
            assert result.offset == 0

        asyncio.run(run_test())

    def test_get_deals_with_category_filter(self, mock_db, mock_api_key, mock_request, sample_products):
        async def run_test():
            from app.routers.deals import get_deals

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [sample_products[2]]
            mock_db.execute.return_value = mock_result

            result = await get_deals(
                request=mock_request,
                category="Fashion",
                min_discount_pct=10.0,
                limit=20,
                offset=0,
                db=mock_db,
                api_key=mock_api_key,
            )

            assert isinstance(result, DealsResponse)
            assert len(result.items) == 1
            assert result.items[0].category == "Fashion"

        asyncio.run(run_test())

    def test_deal_item_from_product(self, sample_product):
        from app.routers.deals import _to_deal_item

        result = _to_deal_item(sample_product)

        assert isinstance(result, DealItem)
        assert result.id == sample_product.id
        assert result.name == sample_product.title
        assert result.price == sample_product.price
        assert result.original_price == Decimal("2499.00")
        assert result.discount_pct is not None
        assert result.discount_pct > 0

    def test_deal_item_no_original_price(self):
        from app.routers.deals import _to_deal_item

        mock_product = MagicMock()
        mock_product.id = 1
        mock_product.title = "Test Product"
        mock_product.price = Decimal("100.00")
        mock_product.currency = "SGD"
        mock_product.source = "shopee_sg"
        mock_product.category = "Electronics"
        mock_product.url = "https://shopee.sg/product/1"
        mock_product.metadata_ = {}
        mock_product.image_url = None

        result = _to_deal_item(mock_product)

        assert result.original_price is None
        assert result.discount_pct is None


class TestStatusRouter:
    """Tests for /v1/status endpoint."""

    def test_get_catalog_status(self, mock_db, mock_api_key, mock_request):
        async def run_test():
            import app.routers.status as status_module
            from app.schemas.status import CatalogStatus, PlatformProductCount, IngestionRunInfo

            mock_result = CatalogStatus(
                total_unique_products=1000,
                platforms=[
                    PlatformProductCount(source="shopee_sg", product_count=500, last_updated=datetime.now(timezone.utc)),
                    PlatformProductCount(source="lazada_sg", product_count=300, last_updated=datetime.now(timezone.utc)),
                    PlatformProductCount(source="carousell", product_count=200, last_updated=datetime.now(timezone.utc)),
                ],
                ingestion_runs=[
                    IngestionRunInfo(
                        source="shopee_sg",
                        last_run_at=datetime.now(timezone.utc),
                        last_run_status="completed",
                        last_rows_inserted=100,
                        last_rows_updated=50,
                    ),
                    IngestionRunInfo(
                        source="lazada_sg",
                        last_run_at=datetime.now(timezone.utc),
                        last_run_status="completed",
                        last_rows_inserted=80,
                        last_rows_updated=20,
                    ),
                ],
                goal_million=1.0,
                progress_percent=0.1,
            )

            with patch.object(status_module, "get_catalog_status", return_value=mock_result):
                result = await status_module.get_catalog_status(
                    request=mock_request,
                    db=mock_db,
                    api_key=mock_api_key,
                )

            assert isinstance(result, CatalogStatus)
            assert result.total_unique_products == 1000
            assert len(result.platforms) == 3
            assert result.goal_million == 1.0
            assert result.progress_percent == 0.1

        asyncio.run(run_test())

    def test_get_catalog_status_empty(self, mock_db, mock_api_key, mock_request):
        async def run_test():
            from app.routers.status import get_catalog_status

            mock_result = MagicMock()
            mock_result.scalar_one.return_value = 0

            mock_platform_result = MagicMock()
            mock_platform_result.all.return_value = []

            mock_last_runs_result = MagicMock()
            mock_last_runs_result.all.return_value = []

            mock_last_run_details_result = MagicMock()
            mock_last_run_details_result.all.return_value = []

            mock_db.execute.side_effect = [
                mock_result,
                mock_platform_result,
                mock_last_runs_result,
                mock_last_run_details_result,
            ]

            result = await get_catalog_status(
                request=mock_request,
                db=mock_db,
                api_key=mock_api_key,
            )

            assert isinstance(result, CatalogStatus)
            assert result.total_unique_products == 0
            assert len(result.platforms) == 0

        asyncio.run(run_test())


class TestCatalogRouter:
    """Tests for /v1/catalog endpoints."""

    def test_catalog_health(self, mock_db, mock_api_key):
        async def run_test():
            from app.routers.catalog import catalog_health
            from app.services.catalog_health import get_catalog_health

            mock_health_data = {
                "generated_at": datetime.now(timezone.utc),
                "total_indexed": 1000,
                "by_platform": {"shopee_sg": 500, "lazada_sg": 300, "carousell": 200},
                "compliance": {
                    "total_products": 1000,
                    "compliant_products": 950,
                    "compliance_rate": 0.95,
                    "by_platform": [],
                    "missing_title": 10,
                    "missing_price": 5,
                    "missing_source": 0,
                    "missing_source_id": 35,
                    "missing_url": 3,
                    "incomplete_products": 50,
                },
                "deduplication": {
                    "total_products": 1000,
                    "products_with_canonical": 100,
                    "duplicate_rate": 0.1,
                    "duplicate_groups": 20,
                    "sample_duplicates": [],
                },
                "freshness": {
                    "total_products": 1000,
                    "stale_products": 50,
                    "stale_rate": 0.05,
                    "re_scrape_count": 10,
                    "by_platform": {"shopee_sg": 20, "lazada_sg": 15, "carousell": 15},
                    "sample_stale": [],
                },
            }

            with patch("app.routers.catalog.get_catalog_health", new_callable=AsyncMock) as mock_get_health:
                mock_get_health.return_value = mock_health_data

                result = await catalog_health(
                    db=mock_db,
                    api_key=mock_api_key,
                )

            assert result.total_indexed == 1000
            assert result.compliance.compliance_rate == 0.95
            assert result.deduplication.duplicate_rate == 0.1
            assert result.compliance.missing_url == 3
            assert result.compliance.incomplete_products == 50

        asyncio.run(run_test())

    def test_list_incomplete_products(self, mock_db, mock_api_key):
        async def run_test():
            from app.routers.catalog import list_incomplete_products

            mock_row = MagicMock()
            mock_row.id = 1
            mock_row.sku = "INCOMPLETE-001"
            mock_row.source = "shopee_sg"
            mock_row.title = ""
            mock_row.price = None
            mock_row.url = "https://shopee.sg/product/1"
            mock_row.is_active = True
            mock_row.updated_at = datetime(2024, 1, 15, tzinfo=timezone.utc)

            mock_result = MagicMock()
            mock_result.all.return_value = [mock_row]
            mock_count_result = MagicMock()
            mock_count_result.scalar_one.return_value = 1

            mock_db.execute.side_effect = [mock_count_result, mock_result]

            result = await list_incomplete_products(
                db=mock_db,
                api_key=mock_api_key,
                source=None,
                limit=20,
                offset=0,
            )

            assert result["total"] == 1
            assert len(result["items"]) == 1
            item = result["items"][0]
            assert item["missing_fields"] == ["title", "price"]
            assert item["sku"] == "INCOMPLETE-001"

        asyncio.run(run_test())

    def test_list_incomplete_products_missing_url(self, mock_db, mock_api_key):
        async def run_test():
            from app.routers.catalog import list_incomplete_products

            mock_row = MagicMock()
            mock_row.id = 2
            mock_row.sku = "NO-URL-001"
            mock_row.source = "lazada_sg"
            mock_row.title = "Test Product"
            mock_row.price = Decimal("99.99")
            mock_row.url = ""
            mock_row.is_active = True
            mock_row.updated_at = datetime(2024, 1, 15, tzinfo=timezone.utc)

            mock_result = MagicMock()
            mock_result.all.return_value = [mock_row]
            mock_count_result = MagicMock()
            mock_count_result.scalar_one.return_value = 1

            mock_db.execute.side_effect = [mock_count_result, mock_result]

            result = await list_incomplete_products(
                db=mock_db,
                api_key=mock_api_key,
                source=None,
                limit=20,
                offset=0,
            )

            assert result["total"] == 1
            item = result["items"][0]
            assert "url" in item["missing_fields"]

        asyncio.run(run_test())


class TestKeysRouter:
    """Tests for /v1/keys endpoints."""

    def test_create_api_key_success(self, mock_db):
        async def run_test():
            from app.routers.keys import create_api_key, ProvisionRequest, ADMIN_SECRET

            mock_api_key = MagicMock()
            mock_api_key.id = "new-key-id"
            mock_api_key.tier = "basic"

            with patch("app.routers.keys.provision_api_key", new_callable=AsyncMock) as mock_provision:
                mock_provision.return_value = ("raw_key_abc123", mock_api_key)

                with patch.object(__import__("app.routers.keys", fromlist=["ADMIN_SECRET"]), "ADMIN_SECRET", "test-secret"):
                    request = ProvisionRequest(
                        developer_id="dev-001",
                        name="Test Developer",
                        tier="basic",
                        admin_secret="test-secret",
                    )

                    result = await create_api_key(
                        body=request,
                        db=mock_db,
                    )

            assert result.tier == "basic"
            assert result.raw_key == "raw_key_abc123"

        asyncio.run(run_test())

    def test_create_api_key_forbidden(self, mock_db):
        async def run_test():
            from app.routers.keys import create_api_key, ProvisionRequest

            with patch("app.routers.keys.get_settings") as mock_settings:
                mock_settings.return_value.jwt_secret_key = "correct-secret"

                request = ProvisionRequest(
                    developer_id="dev-001",
                    name="Test Developer",
                    tier="basic",
                    admin_secret="wrong-secret",
                )

                with pytest.raises(HTTPException) as exc_info:
                    await create_api_key(
                        body=request,
                        db=mock_db,
                    )

            assert exc_info.value.status_code == 403

        asyncio.run(run_test())


class TestProductSchemas:
    """Tests for product schemas."""

    def test_product_response_from_attributes(self):
        from app.schemas.product import ProductResponse

        data = {
            "id": 1,
            "sku": "SKU-001",
            "source": "shopee_sg",
            "merchant_id": "merchant_001",
            "name": "Test Product",
            "price": Decimal("99.99"),
            "currency": "SGD",
            "buy_url": "https://shopee.sg/product/1",
            "affiliate_url": "https://shopee.sg/product/1?ref=buywhere",
            "image_url": "https://shopee.sg/image.jpg",
            "category": "Electronics",
            "category_path": ["Electronics", "Phones"],
            "availability": True,
            "metadata": {"condition": "new"},
            "updated_at": datetime.now(timezone.utc),
        }

        response = ProductResponse(**data)
        assert response.id == 1
        assert response.sku == "SKU-001"
        assert response.price == Decimal("99.99")
        assert response.availability is True

    def test_product_list_response(self):
        from app.schemas.product import ProductListResponse, ProductResponse

        items = [
            ProductResponse(
                id=1,
                sku="SKU-001",
                source="shopee_sg",
                merchant_id="m1",
                name="Product 1",
                price=Decimal("99.99"),
                currency="SGD",
                buy_url="https://shopee.sg/1",
                availability=True,
                updated_at=datetime.now(timezone.utc),
                affiliate_url=None,
            ),
            ProductResponse(
                id=2,
                sku="SKU-002",
                source="lazada_sg",
                merchant_id="m2",
                name="Product 2",
                price=Decimal("149.99"),
                currency="SGD",
                buy_url="https://lazada.sg/2",
                availability=True,
                updated_at=datetime.now(timezone.utc),
                affiliate_url=None,
            ),
        ]

        response = ProductListResponse(total=2, limit=20, offset=0, items=items)
        assert response.total == 2
        assert len(response.items) == 2

    def test_compare_response(self):
        from app.schemas.product import CompareResponse, CompareMatch

        matches = [
            CompareMatch(
                id=2,
                sku="SKU-002",
                source="lazada_sg",
                merchant_id="m2",
                name="Lazada Product",
                price=Decimal("149.99"),
                currency="SGD",
                buy_url="https://lazada.sg/2",
                availability=True,
                updated_at=datetime.now(timezone.utc),
                match_score=0.95,
            )
        ]

        response = CompareResponse(
            source_product_id=1,
            source_product_name="Shopee Product",
            matches=matches,
            total_matches=1,
        )

        assert response.source_product_id == 1
        assert response.total_matches == 1
        assert response.matches[0].match_score == 0.95

    def test_category_node(self):
        node = CategoryNode(name="Electronics", count=100, children=[])
        assert node.name == "Electronics"
        assert node.count == 100

    def test_category_response(self):
        categories = [
            CategoryNode(name="Electronics", count=100),
            CategoryNode(name="Fashion", count=50),
        ]
        response = CategoryResponse(categories=categories, total=2)
        assert response.total == 2


class TestDealSchemas:
    """Tests for deal schemas."""

    def test_deal_item(self):
        item = DealItem(
            id=1,
            name="iPhone 14 Pro",
            price=Decimal("1999.00"),
            original_price=Decimal("2499.00"),
            discount_pct=20.0,
            currency="SGD",
            source="shopee_sg",
            category="Electronics",
            buy_url="https://shopee.sg/product/1",
            affiliate_url="https://shopee.sg/product/1?ref=buywhere",
            image_url="https://shopee.sg/image.jpg",
            metadata={"condition": "new"},
        )

        assert item.discount_pct == 20.0
        assert item.original_price == Decimal("2499.00")

    def test_deals_response(self):
        items = [
            DealItem(
                id=1,
                name="Product 1",
                price=Decimal("99.00"),
                original_price=Decimal("199.00"),
                discount_pct=50.0,
                currency="SGD",
                source="shopee_sg",
                category="Electronics",
                buy_url="https://shopee.sg/1",
                affiliate_url=None,
                image_url=None,
                metadata=None,
            )
        ]

        response = DealsResponse(total=1, limit=20, offset=0, items=items)
        assert response.total == 1
        assert len(response.items) == 1
        assert response.items[0].discount_pct == 50.0


class TestStatusSchemas:
    """Tests for status schemas."""

    def test_catalog_status(self):
        platforms = [
            PlatformProductCount(source="shopee_sg", product_count=500, last_updated=datetime.now(timezone.utc)),
            PlatformProductCount(source="lazada_sg", product_count=300, last_updated=datetime.now(timezone.utc)),
        ]
        ingestion_runs = [
            IngestionRunInfo(
                source="shopee_sg",
                last_run_at=datetime.now(timezone.utc),
                last_run_status="completed",
                last_rows_inserted=100,
                last_rows_updated=50,
            )
        ]

        status = CatalogStatus(
            total_unique_products=800,
            platforms=platforms,
            ingestion_runs=ingestion_runs,
            goal_million=1.0,
            progress_percent=0.08,
        )

        assert status.total_unique_products == 800
        assert len(status.platforms) == 2
        assert status.goal_million == 1.0
        assert status.progress_percent == 0.08


class TestPriceHistoryRouter:
    """Tests for /v1/products/{product_id}/price-history endpoint."""

    def test_get_price_history_found(self, mock_db, mock_api_key, mock_request, mock_cache, sample_product):
        from app.routers.products import get_product_price_history
        from app.schemas.product import PriceHistoryResponse, PricePoint
        from app.models.product import PriceHistory

        async def run_test():
            mock_cache["get"].return_value = None

            product_result = MagicMock()
            product_result.scalar_one_or_none.return_value = sample_product

            stats_result = MagicMock()
            stats_result.tuple.return_value = (
                Decimal("1899.00"),
                Decimal("2099.00"),
                Decimal("1999.00"),
                5,
            )

            price_history_records = [
                MagicMock(spec=PriceHistory, price=Decimal("1999.00"), currency="SGD", recorded_at=datetime(2024, 1, 15, tzinfo=timezone.utc)),
                MagicMock(spec=PriceHistory, price=Decimal("1899.00"), currency="SGD", recorded_at=datetime(2024, 1, 10, tzinfo=timezone.utc)),
            ]
            history_result = MagicMock()
            history_result.scalars.return_value.all.return_value = price_history_records

            def execute_side_effect(query):
                q_str = str(query)
                if "is_active" in q_str:
                    return product_result
                elif "min(" in q_str or "max(" in q_str or "avg(" in q_str or "count(" in q_str:
                    return stats_result
                else:
                    return history_result

            mock_db.execute.side_effect = execute_side_effect

            result = await get_product_price_history(
                request=mock_request,
                product_id=1,
                days=30,
                limit=100,
                db=mock_db,
                api_key=mock_api_key,
            )

            assert isinstance(result, PriceHistoryResponse)
            assert result.product_id == sample_product.id
            assert result.product_name == sample_product.title
            assert result.currency == sample_product.currency
            assert result.current_price == sample_product.price
            assert len(result.price_points) == 2
            assert result.min_price == Decimal("1899.00")
            assert result.max_price == Decimal("2099.00")
            assert result.total_records == 5

        asyncio.run(run_test())

    def test_get_price_history_not_found(self, mock_db, mock_api_key, mock_request, mock_cache):
        from app.routers.products import get_product_price_history

        async def run_test():
            mock_cache["get"].return_value = None

            product_result = MagicMock()
            product_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = product_result

            with pytest.raises(HTTPException) as exc_info:
                await get_product_price_history(
                    request=mock_request,
                    product_id=999,
                    days=30,
                    limit=100,
                    db=mock_db,
                    api_key=mock_api_key,
                )

            assert exc_info.value.status_code == 404
            assert "Product not found" in str(exc_info.value.detail)

        asyncio.run(run_test())


class TestPriceHistorySchemas:
    """Tests for price history schemas."""

    def test_price_point(self):
        from app.schemas.product import PricePoint

        point = PricePoint(
            price=Decimal("1999.00"),
            currency="SGD",
            recorded_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        assert point.price == Decimal("1999.00")
        assert point.currency == "SGD"
        assert point.recorded_at == datetime(2024, 1, 15, tzinfo=timezone.utc)

    def test_price_history_response(self):
        from app.schemas.product import PriceHistoryResponse, PricePoint

        price_points = [
            PricePoint(
                price=Decimal("1999.00"),
                currency="SGD",
                recorded_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
            ),
            PricePoint(
                price=Decimal("1899.00"),
                currency="SGD",
                recorded_at=datetime(2024, 1, 10, tzinfo=timezone.utc),
            ),
        ]

        response = PriceHistoryResponse(
            product_id=1,
            product_name="iPhone 14 Pro",
            currency="SGD",
            current_price=Decimal("1999.00"),
            price_points=price_points,
            total_records=5,
            min_price=Decimal("1899.00"),
            max_price=Decimal("2099.00"),
            avg_price=Decimal("1999.00"),
        )

        assert response.product_id == 1
        assert response.product_name == "iPhone 14 Pro"
        assert response.current_price == Decimal("1999.00")
        assert len(response.price_points) == 2
        assert response.min_price == Decimal("1899.00")
        assert response.max_price == Decimal("2099.00")
        assert response.avg_price == Decimal("1999.00")
