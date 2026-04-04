from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from decimal import Decimal
from datetime import datetime
from enum import Enum


class PriceTrend(str):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class PriceHistoryEntry(BaseModel):
    price: Decimal
    currency: str
    platform: str = Field(..., description="Source platform (e.g. shopee_sg, lazada_sg)")
    scraped_at: datetime = Field(..., description="Timestamp when price was scraped")

    model_config = {"from_attributes": True, "populate_by_name": True}


class PriceHistoryResponse(BaseModel):
    product_id: int
    entries: List[PriceHistoryEntry]
    total: int


class PriceStats(BaseModel):
    current_price: Decimal
    currency: str
    min_price: Decimal
    max_price: Decimal
    avg_price: Decimal
    price_trend: str = Field(..., description="Price trend over 30 days: 'up', 'down', or 'stable'")
    price_trend_pct: Optional[float] = Field(None, description="Percentage change over 30 days")
    record_count: int

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    id: int
    sku: str
    source: str
    merchant_id: str
    name: str = Field(..., description="Product title")
    description: Optional[str] = None
    price: Decimal
    currency: str
    price_sgd: Optional[Decimal] = Field(None, description="Price normalized to SGD")
    buy_url: str = Field(..., description="Direct purchase URL")
    affiliate_url: Optional[str] = Field(None, description="Tracked affiliate URL (use this to send traffic)")
    image_url: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    category_path: Optional[List[str]] = None
    rating: Optional[Decimal] = None
    review_count: Optional[int] = Field(None, description="Number of reviews from aggregated sources")
    avg_rating: Optional[Decimal] = Field(None, description="Average rating from aggregated sources (0-5)")
    rating_source: Optional[str] = Field(None, description="Source of the aggregated rating (e.g. 'scraped', 'platform_api')")
    is_available: bool = Field(..., description="Whether product is currently in stock and available for purchase")
    last_checked: Optional[datetime] = Field(None, description="Timestamp when availability was last checked")
    metadata: Optional[Any] = None
    updated_at: datetime
    price_trend: Optional[str] = Field(None, description="30-day price trend: 'up', 'down', or 'stable'")

    model_config = {"from_attributes": True}


class FacetBucket(BaseModel):
    value: str
    count: int


class RatingFacetBucket(BaseModel):
    min_rating: float
    max_rating: float
    count: int


class PriceFacetBucket(BaseModel):
    min_price: Decimal
    max_price: Optional[Decimal]
    count: int


class FacetCounts(BaseModel):
    categories: List[FacetBucket] = Field(default_factory=list)
    platforms: List[FacetBucket] = Field(default_factory=list)
    brands: List[FacetBucket] = Field(default_factory=list)
    rating_ranges: List[RatingFacetBucket] = Field(default_factory=list)
    price_ranges: List[PriceFacetBucket] = Field(default_factory=list)


class ProductListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[ProductResponse]
    has_more: bool = False
    facets: Optional[FacetCounts] = Field(None, description="Facet counts for filtering")
    highlights: Optional[Dict[str, str]] = Field(None, description="Highlighted search terms per product ID")


class SearchSuggestion(BaseModel):
    text: str = Field(..., description="Suggestion text")
    score: float = Field(..., description="Relevance score (higher = more relevant)")
    source: str = Field(..., description="Source of suggestion: title, brand, or category")


class SearchSuggestionResponse(BaseModel):
    query: str = Field(..., description="Original query")
    suggestions: List[SearchSuggestion] = Field(..., description="Top search suggestions")
    total: int = Field(..., description="Total number of suggestions")


class AutocompleteSuggestion(BaseModel):
    suggestion: str = Field(..., description="Completion text")
    product_count: int = Field(..., description="Number of products matching this suggestion")


class AutocompleteResponse(BaseModel):
    suggestions: List[AutocompleteSuggestion] = Field(..., description="Top autocomplete suggestions")
    total: int = Field(..., description="Total number of suggestions returned")


class CategoryNode(BaseModel):
    id: str
    name: str
    slug: str
    parent_id: Optional[str] = None
    count: int = 0
    children: List["CategoryNode"] = []


class TaxonomyCategory(BaseModel):
    id: str
    name: str
    product_count: int = 0
    subcategories: List["TaxonomySubCategory"] = []


class TaxonomySubCategory(BaseModel):
    id: str
    name: str
    product_count: int


class TaxonomyResponse(BaseModel):
    categories: List[TaxonomyCategory]
    total: int
    version: str = "1.0"


class CategoryResponse(BaseModel):
    categories: List[CategoryNode]
    total: int


class ProductSearchParams(BaseModel):
    q: Optional[str] = Field(None, description="Full-text search query")
    category: Optional[str] = Field(None, description="Filter by category name")
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    source: Optional[str] = Field(None, description="Filter by source (lazada_sg, shopee_sg, etc.)")
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class ProductIngestItem(BaseModel):
    sku: str = Field(..., description="Unique product identifier within the source")
    merchant_id: str = Field(..., description="Merchant/platform shop identifier")
    title: str = Field(..., description="Product title")
    description: Optional[str] = None
    price: Decimal = Field(..., ge=0)
    currency: str = Field(default="SGD")
    url: str = Field(..., description="Direct purchase URL")
    category: Optional[str] = None
    category_path: Optional[List[str]] = None
    image_url: Optional[str] = None
    is_active: bool = Field(default=True)
    metadata: Optional[Any] = None


class ProductIngestRequest(BaseModel):
    source: str = Field(..., description="Source platform (e.g. shopee_sg, lazada_sg, carousell)")
    products: List[ProductIngestItem] = Field(..., min_length=1, max_length=1000)


class ProductIngestResponse(BaseModel):
    run_id: int
    rows_inserted: int
    rows_updated: int
    rows_failed: int
    errors: List[str] = []


class CompareMatch(BaseModel):
    id: int
    sku: str
    source: str
    merchant_id: str
    name: str = Field(..., description="Product title")
    description: Optional[str] = None
    price: Decimal
    currency: str
    buy_url: str
    affiliate_url: Optional[str] = None
    image_url: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    category_path: Optional[List[str]] = None
    rating: Optional[Decimal] = None
    is_available: bool
    last_checked: Optional[datetime] = None
    metadata: Optional[Any] = None
    updated_at: datetime
    match_score: float = Field(..., description="Similarity score (0-1)")
    savings_vs_most_expensive: Optional[float] = Field(None, description="Price savings vs most expensive option")
    savings_pct: Optional[float] = Field(None, description="Percentage savings vs most expensive option")

    model_config = {"from_attributes": True}


class CompareHighlights(BaseModel):
    cheapest: Optional[CompareMatch] = Field(None, description="Cheapest option among matches")
    best_rated: Optional[CompareMatch] = Field(None, description="Highest rated option among matches")
    fastest_shipping: Optional[CompareMatch] = Field(None, description="Fastest shipping option (from metadata)")

    model_config = {"from_attributes": True}


class CompareSearchMatch(BaseModel):
    id: int
    sku: str
    source: str
    merchant_id: str
    name: str = Field(..., description="Product title")
    description: Optional[str] = None
    price: Decimal
    currency: str
    buy_url: str
    affiliate_url: Optional[str] = None
    image_url: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    category_path: Optional[List[str]] = None
    rating: Optional[Decimal] = None
    is_available: bool
    last_checked: Optional[datetime] = None
    metadata: Optional[Any] = None
    updated_at: datetime
    match_score: float = Field(..., description="Similarity score (0-1)")

    model_config = {"from_attributes": True}


class CompareSearchResponse(BaseModel):
    query: str
    items: List[CompareSearchMatch]
    total: int
    cheapest_product_id: Optional[int] = None
    best_rated_product_id: Optional[int] = None
    fastest_shipping_product_id: Optional[int] = None


class CompareResponse(BaseModel):
    source_product_id: int
    source_product_name: str
    matches: List[CompareMatch]
    total_matches: int
    highlights: Optional[CompareHighlights] = Field(None, description="Notable highlights across compared products")


class ProductMatchResponse(BaseModel):
    id: int
    source_product_id: int
    matched_product_id: int
    confidence_score: float
    match_method: str
    name_similarity: Optional[float] = None
    image_similarity: Optional[float] = None
    price_diff_pct: Optional[float] = None
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductMatchesResponse(BaseModel):
    product_id: int
    matches: List[CompareMatch]
    total_matches: int


class CompareMatrixEntry(BaseModel):
    source_product_id: int
    source_product_name: str
    matches: List[CompareMatch]
    total_matches: int


class CompareMatrixResponse(BaseModel):
    comparisons: List[CompareMatrixEntry]
    total_products: int
    highlights: Optional[CompareHighlights] = Field(None, description="Notable highlights across compared products")


class CompareMatrixRequest(BaseModel):
    product_ids: List[int] = Field(..., min_length=2, max_length=20, description="List of product IDs to compare (2-20)")
    min_price: Optional[Decimal] = Field(None, ge=0, description="Minimum price filter for matches")
    max_price: Optional[Decimal] = Field(None, ge=0, description="Maximum price filter for matches")


class CompareDiffRequest(BaseModel):
    product_ids: List[int] = Field(..., min_length=2, max_length=5, description="List of 2-5 product IDs to compare directly")
    include_image_similarity: bool = Field(default=False, description="Include image similarity computation")


class FieldDiff(BaseModel):
    field: str
    values: List[Any] = Field(..., description="Value per product in order provided")
    all_identical: bool = Field(..., description="True if all products have the same value for this field")


class CompareDiffEntry(BaseModel):
    id: int
    sku: str
    source: str
    merchant_id: str
    name: str
    description: Optional[str] = None
    price: Decimal
    currency: str
    buy_url: str
    affiliate_url: Optional[str] = None
    image_url: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    category_path: Optional[List[str]] = None
    rating: Optional[Decimal] = None
    is_available: bool
    last_checked: Optional[datetime] = None
    metadata: Optional[Any] = None
    updated_at: datetime
    price_rank: int = Field(..., description="Price rank among the compared products (1 = cheapest)")

    model_config = {"from_attributes": True}


class CompareDiffResponse(BaseModel):
    products: List[CompareDiffEntry]
    field_diffs: List[FieldDiff] = Field(..., description="Fields that differ across products")
    identical_fields: List[str] = Field(..., description="Fields that are identical across all products")
    cheapest_product_id: int
    most_expensive_product_id: int
    price_spread: Decimal = Field(..., description="Price difference between cheapest and most expensive")
    price_spread_pct: float = Field(..., description="Price spread as percentage of cheapest price")


class TrendingMatch(BaseModel):
    id: int
    sku: str
    source: str
    merchant_id: str
    name: str = Field(..., description="Product title")
    description: Optional[str] = None
    price: Decimal
    currency: str
    buy_url: str
    affiliate_url: Optional[str] = None
    image_url: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    category_path: Optional[List[str]] = None
    rating: Optional[Decimal] = None
    is_available: bool
    last_checked: Optional[datetime] = None
    metadata: Optional[Any] = None
    updated_at: datetime
    view_count: int = Field(0, description="Number of views/queries for this product in the trending period")
    click_count: int = Field(0, description="Number of affiliate link clicks for this product")

    model_config = {"from_attributes": True}


class PlatformDistribution(BaseModel):
    platform: str
    count: int
    percentage: float


class CategoryBreakdown(BaseModel):
    category: str
    count: int
    percentage: float


class TrendingResponse(BaseModel):
    period: str = Field(..., description="Trending period: 24h, 7d, or 30d")
    category: Optional[str] = None
    items: List[TrendingMatch]
    total: int
    platform_distribution: List[PlatformDistribution] = Field(
        default_factory=list, description="Distribution of trending products across platforms"
    )
    category_breakdown: List[CategoryBreakdown] = Field(
        default_factory=list, description="Distribution of trending products across categories"
    )


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    tier: str
    is_active: bool
    rate_limit: Optional[int] = None
    allowed_origins: Optional[List[str]] = None
    rotated_from_key_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    request_count: int = 0
    created_at: datetime
    last_used_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Descriptive name for this API key")
    rate_limit: Optional[int] = Field(None, description="Requests per minute rate limit")
    allowed_origins: Optional[List[str]] = Field(None, description="Allowed CORS origins")


class ApiKeyCreateResponse(BaseModel):
    key_id: str
    raw_key: str = Field(..., description="Store this securely — it will not be shown again")
    name: str
    tier: str
    message: str


class ApiKeyRotateResponse(BaseModel):
    key_id: str
    raw_key: str = Field(..., description="Store this securely — it will not be shown again")
    name: str
    tier: str
    expires_at: Optional[datetime] = Field(None, description="When the old key expires and new key becomes required")
    message: str


class ApiKeyListResponse(BaseModel):
    keys: List[ApiKeyResponse]
    total: int


class DeveloperSignupRequest(BaseModel):
    email: str = Field(..., description="Developer email address", max_length=255)
    name: str = Field(..., min_length=1, max_length=100, description="Descriptive name for the first API key")


class DeveloperSignupResponse(BaseModel):
    developer_id: str
    email: str
    plan: str
    key_id: str
    raw_key: str = Field(..., description="Store this securely — it will not be shown again")
    name: str
    tier: str
    message: str


class DeveloperResponse(BaseModel):
    id: str
    email: str
    plan: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DeveloperMeResponse(BaseModel):
    developer: DeveloperResponse
    api_keys: List[ApiKeyResponse]
    total_keys: int


class RecommendationMatch(BaseModel):
    id: int
    sku: str
    source: str
    merchant_id: str
    name: str = Field(..., description="Product title")
    description: Optional[str] = None
    price: Decimal
    currency: str
    buy_url: str
    affiliate_url: Optional[str] = Field(None, description="Tracked affiliate URL (use this to send traffic)")
    image_url: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    category_path: Optional[List[str]] = None
    rating: Optional[Decimal] = None
    is_available: bool
    last_checked: Optional[datetime] = None
    metadata: Optional[Any] = None
    updated_at: datetime
    relevance_score: float = Field(..., description="Relevance score (0-1) combining TF-IDF title similarity, category match, and price proximity")

    model_config = {"from_attributes": True}


class RecommendationsResponse(BaseModel):
    source_product_id: int
    source_product_name: str
    items: List[RecommendationMatch]
    total: int


class StockStatus(str, Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    PRE_ORDER = "pre_order"


class PlatformAvailability(BaseModel):
    platform: str = Field(..., description="Source platform (e.g. shopee_sg, lazada_sg)")
    status: StockStatus = Field(..., description="Stock status: in_stock, low_stock, out_of_stock, pre_order")
    last_checked_at: Optional[datetime] = Field(None, description="Timestamp when availability was last checked")
    raw_stock_info: Optional[Any] = Field(None, description="Raw stock info from metadata if available")

    model_config = {"from_attributes": True}


class ProductAvailabilityResponse(BaseModel):
    product_id: int
    canonical_id: Optional[int] = Field(None, description="Canonical product group ID if grouped")
    platforms: List[PlatformAvailability] = Field(..., description="Per-platform stock availability")
    overall_status: StockStatus = Field(..., description="Worst-case stock status across all platforms")
    last_checked_at: Optional[datetime] = Field(None, description="Most recent check timestamp across platforms")
    is_stale: bool = Field(False, description="Whether this product has not been checked in more than 7 days")

    model_config = {"from_attributes": True}


class BulkAvailabilityRequest(BaseModel):
    product_ids: List[int] = Field(..., min_length=1, max_length=100, description="List of product IDs to check (1-100)")


class BulkAvailabilityResponse(BaseModel):
    products: List[ProductAvailabilityResponse]
    total: int


class PriceComparisonItem(BaseModel):
    id: int
    source: str
    merchant_id: str
    name: str = Field(..., description="Product title")
    price: Decimal
    currency: str
    shipping_cost: Optional[Decimal] = Field(None, description="Shipping cost in local currency")
    total_cost: Decimal = Field(..., description="Total cost: price + shipping")
    buy_url: str
    affiliate_url: Optional[str] = Field(None, description="Tracked affiliate URL")
    image_url: Optional[str] = None
    rating: Optional[Decimal] = Field(None, description="Seller rating (0-5)")
    delivery_estimate: Optional[str] = Field(None, description="Delivery estimate (e.g. '2-5 days')")
    is_available: bool
    last_checked: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PriceComparisonResponse(BaseModel):
    source_product_id: int
    source_product_name: str
    items: List[PriceComparisonItem]
    total: int
    cheapest_product_id: Optional[int] = None
    fastest_delivery_product_id: Optional[int] = None
    best_rated_product_id: Optional[int] = None


class MerchantSummary(BaseModel):
    merchant_id: str = Field(..., description="Unique merchant identifier")
    merchant_name: str = Field(..., description="Merchant/store name")
    platform: str = Field(..., description="Source platform (e.g. shopee_sg, lazada_sg)")
    product_count: int = Field(..., description="Number of active products from this merchant")
    categories: List[str] = Field(..., description="Distinct product categories from this merchant")
    avg_rating: Optional[float] = Field(None, description="Average product rating across merchant's products (0-5 scale)")
    last_scraped_at: Optional[datetime] = Field(None, description="Timestamp of most recently scraped product from this merchant")

    model_config = {"from_attributes": True}


class MerchantListResponse(BaseModel):
    merchants: List[MerchantSummary]
    total: int
    limit: int
    offset: int
    has_more: bool = False


class BulkLookupMatch(BaseModel):
    id: int
    sku: str
    source: str
    merchant_id: str
    name: str = Field(..., description="Product title")
    description: Optional[str] = None
    price: Decimal
    currency: str
    buy_url: str
    affiliate_url: Optional[str] = None
    image_url: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    category_path: Optional[List[str]] = None
    rating: Optional[Decimal] = None
    is_available: bool
    last_checked: Optional[datetime] = None
    metadata: Optional[Any] = None
    updated_at: datetime
    match_score: float = Field(..., description="Confidence score (0-1): 1.0 for exact SKU/URL/UPC match, lower for fuzzy matches")

    model_config = {"from_attributes": True}


class BulkLookupResultItem(BaseModel):
    identifier: str = Field(..., description="The identifier that was looked up")
    identifier_type: str = Field(..., description="Type: 'sku', 'upc', or 'url'")
    status: str = Field(..., description="Result status: 'found', 'not_found', or 'multiple'")
    match: Optional[BulkLookupMatch] = None
    match_count: int = Field(0, description="Number of matches found (0 if not found, >1 if multiple)")


class BulkLookupRequest(BaseModel):
    identifiers: List[str] = Field(..., min_length=1, max_length=100, description="List of SKU, UPC, or product URL to look up (max 100)")


class BulkLookupResponse(BaseModel):
    results: List[BulkLookupResultItem]
    total: int
    found: int
    not_found: int
    multiple: int


class RatingDistributionBucket(BaseModel):
    stars: int = Field(..., description="Star rating (1-5)")
    count: int = Field(..., description="Number of reviews with this star rating")
    percentage: float = Field(..., description="Percentage of total reviews")


class ReviewSource(BaseModel):
    source: str = Field(..., description="Source of the review (e.g. 'shopee', 'lazada', 'platform_api')")
    review_count: Optional[int] = Field(None, description="Number of reviews from this source")
    avg_rating: Optional[Decimal] = Field(None, description="Average rating from this source (0-5)")
    last_scraped: Optional[datetime] = Field(None, description="When this review data was last scraped")


class ProductReviewsResponse(BaseModel):
    product_id: int
    review_count: Optional[int] = Field(None, description="Total aggregated review count")
    avg_rating: Optional[Decimal] = Field(None, description="Aggregated average rating (0-5)")
    rating_source: Optional[str] = Field(None, description="Primary source of rating data")
    sentiment_score: Optional[float] = Field(None, description="Sentiment score derived from review text (0-1 scale, higher = more positive)")
    rating_distribution: List[RatingDistributionBucket] = Field(default_factory=list, description="Star rating distribution (1-5 stars)")
    sources: List[ReviewSource] = Field(default_factory=list, description="Per-source review breakdown")


class BrandSummary(BaseModel):
    name: str = Field(..., description="Brand name")
    product_count: int = Field(..., description="Number of active products from this brand")
    avg_price: Optional[Decimal] = Field(None, description="Average product price for this brand")
    top_category: Optional[str] = Field(None, description="Most common category for this brand")
    sources: List[str] = Field(default_factory=list, description="Source platforms where this brand appears")

    model_config = {"from_attributes": True}


class BrandListResponse(BaseModel):
    brands: List[BrandSummary]
    total: int
    limit: int
    offset: int


class SourceSummary(BaseModel):
    source: str = Field(..., description="Source platform identifier (e.g. shopee_sg, lazada_sg)")
    display_name: str = Field(..., description="Human-readable platform name")
    product_count: int = Field(..., description="Number of active products from this source")
    merchant_count: int = Field(..., description="Number of distinct merchants on this source")
    avg_price: Optional[Decimal] = Field(None, description="Average product price on this source")
    last_scraped_at: Optional[datetime] = Field(None, description="Most recent product scrape timestamp")
    status: str = Field(..., description="Source status: active, degraded, or inactive")

    model_config = {"from_attributes": True}


class SourceListResponse(BaseModel):
    sources: List[SourceSummary]
    total: int


class EndpointUsage(BaseModel):
    endpoint: str = Field(..., description="API endpoint path")
    method: str = Field(..., description="HTTP method")
    count: int = Field(..., description="Number of requests to this endpoint")
    avg_response_time_ms: float = Field(..., description="Average response time in milliseconds")


class UsageStats(BaseModel):
    requests_today: int = Field(0, description="Number of requests today")
    requests_this_week: int = Field(0, description="Number of requests this week")
    requests_this_month: int = Field(0, description="Number of requests this month")
    total_requests: int = Field(0, description="Total requests all time")
    quota_limit: int = Field(..., description="Monthly quota limit")
    quota_remaining: int = Field(..., description="Remaining monthly quota")
    quota_used_pct: float = Field(..., description="Percentage of monthly quota used")
    top_endpoints: List[EndpointUsage] = Field(default_factory=list, description="Top 10 endpoints by request count")
    avg_response_time_ms: float = Field(0.0, description="Average response time across all requests in ms")
    alert_triggered: bool = Field(False, description="Whether 80% quota alert has been triggered")


class DeveloperUsageResponse(BaseModel):
    developer_id: str
    key_id: str
    key_name: str
    tier: str
    usage: UsageStats
    alert_config: dict = Field(default_factory=dict, description="Alert configuration with 80% threshold")


class BulkImportItem(BaseModel):
    sku: str = Field(..., description="Unique product SKU for this merchant")
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: Decimal = Field(..., gt=Decimal("0"), description="Product price (must be > 0)")
    currency: str = Field(default="SGD", description="ISO 4217 currency code")
    url: str = Field(..., description="Direct product URL")
    image_url: Optional[str] = Field(None, description="Product image URL")
    category: Optional[str] = Field(None, description="Primary category")
    category_path: Optional[List[str]] = Field(None, description="Category hierarchy")
    brand: Optional[str] = Field(None, description="Brand name")
    is_active: bool = Field(default=True, description="Whether product is active/listed")
    is_available: Optional[bool] = Field(None, description="Whether product is in stock")
    metadata: Optional[Any] = Field(None, description="Additional product metadata")


class BulkImportRequest(BaseModel):
    source: str = Field(..., description="Source platform (e.g., merchant_own, shopee_sg)")
    products: List[BulkImportItem] = Field(..., min_length=1, max_length=1000)


class BulkImportError(BaseModel):
    index: int
    sku: str
    error: str
    code: str = Field(default="UNKNOWN_ERROR", description="Machine-readable error code")


class BulkImportResponse(BaseModel):
    status: str = Field(..., description="Status: completed, failed, or completed_with_errors")
    rows_inserted: int = Field(default=0, description="Number of new rows inserted")
    rows_updated: int = Field(default=0, description="Number of existing rows updated")
    rows_failed: int = Field(default=0, description="Number of rows that failed")
    errors: List[BulkImportError] = Field(default_factory=list, description="Error details for failed rows")
