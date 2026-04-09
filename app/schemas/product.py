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
    average_price: Decimal
    min_price: Decimal
    max_price: Decimal
    price_change_24h: Optional[Decimal] = None
    price_change_7d: Optional[Decimal] = None
    price_change_30d: Optional[Decimal] = None


class PricePredictionResponse(BaseModel):
    product_id: int
    predicted_price: Decimal
    confidence: float
    prediction_date: datetime
    factors: List[str]


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
    converted_price: Optional[Decimal] = Field(None, description="Price converted to requested currency (when ?currency= param is used)")
    converted_currency: Optional[str] = Field(None, description="Currency of converted_price")
    buy_url: str = Field(..., description="Direct purchase URL")
    affiliate_url: Optional[str] = Field(None, description="Tracked affiliate URL (use this to send traffic)")
    image_url: Optional[str] = None
    barcode: Optional[str] = Field(None, description="UPC/EAN barcode for the product")
    brand: Optional[str] = None
    category: Optional[str] = None
    category_path: Optional[List[str]] = None
    rating: Optional[Decimal] = None
    review_count: Optional[int] = Field(None, description="Number of reviews from aggregated sources")
    avg_rating: Optional[Decimal] = Field(None, description="Average rating from aggregated sources (0-5)")
    rating_source: Optional[str] = Field(None, description="Source of the aggregated rating (e.g. 'scraped', 'platform_api')")
    is_available: bool = Field(..., description="Whether product is currently in stock and available for purchase")
    in_stock: Optional[bool] = Field(None, description="Whether product is in stock")
    stock_level: Optional[str] = Field(None, description="Stock level: low, medium, or high")
    last_checked: Optional[datetime] = Field(None, description="Timestamp when availability was last checked")
    data_updated_at: Optional[datetime] = Field(None, description="Timestamp when product data was last updated")
    availability_prediction: Optional[str] = Field(None, description="Predicted availability based on historical patterns (e.g., 'likely_in_stock', 'likely_out_of_stock')")
    competitor_count: Optional[int] = Field(None, description="Number of platforms selling the same product")
    confidence_score: Optional[float] = Field(None, description="Confidence score of search match (0-1)")
    metadata: Optional[Any] = None
    updated_at: datetime
    price_trend: Optional[str] = Field(None, description="30-day price trend: 'up', 'down', or 'stable'")


class SearchFiltersResponse(BaseModel):
    categories: List[Any]
    brands: List[Any]
    platforms: List[Any]
    countries: List[Any]
    price_ranges: List[Any]
    rating_ranges: List[Any]
    price_min: Decimal
    price_max: Decimal


class ProductListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[ProductResponse]
    has_more: bool = False
    facets: Optional[Any] = None
    highlights: Optional[Dict[str, str]] = None


class V1ProductSearchResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[Any]
    has_more: bool
    meta: Any


class ProductFeedCursorResponse(BaseModel):
    items: List[ProductResponse]
    next_cursor: Optional[str]
    has_more: bool


class SearchSuggestionResponse(BaseModel):
    suggestions: List[str]
    total: int


class AutocompleteResponse(BaseModel):
    query: str
    suggestions: List[Any]
    total: int


class TaxonomyResponse(BaseModel):
    taxonomy: Dict[str, Any]


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    level: int
    product_count: int
    is_active: bool


class ProductIngestResponse(BaseModel):
    ingested: int
    updated: int
    failed: int
    errors: List[str]


class CompareSearchResponse(BaseModel):
    query: str
    items: List[Any]
    total: int
    cheapest_product_id: Optional[int] = None
    best_rated_product_id: Optional[int] = None
    fastest_shipping_product_id: Optional[int] = None


class CompareResponse(BaseModel):
    id: int
    name: str
    price: Decimal
    currency: str
    buy_url: str
    image_url: Optional[str] = None
    brand: Optional[str] = None
    rating: Optional[Decimal] = None


class ProductMatchResponse(BaseModel):
    id: int
    name: str
    price: Decimal
    currency: str
    match_score: float


class ProductMatchesResponse(BaseModel):
    product_id: int
    matches: List[ProductMatchResponse]
    total: int


class SimilarProductsResponse(BaseModel):
    product_id: int
    similar_products: List[Any]
    total: int


class CompareMatch(BaseModel):
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
    is_available: bool
    metadata: Optional[Any] = None
    updated_at: datetime
    match_score: float


class CompareHighlights(BaseModel):
    cheapest: Optional[CompareMatch] = None
    best_rated: Optional[CompareMatch] = None
    fastest_shipping: Optional[CompareMatch] = None


class CompareMatrixResponse(BaseModel):
    comparisons: List[Any]
    total_products: int
    highlights: Optional[Any] = None


class CompareDiffResponse(BaseModel):
    products: List[Any]
    field_diffs: List[Any]
    identical_fields: List[str]
    cheapest_product_id: int
    most_expensive_product_id: int
    price_spread: Decimal
    price_spread_pct: float


class TrendingResponse(BaseModel):
    period: str
    category: Optional[str] = None
    items: List[Any]
    total: int
    platform_distribution: List[Any]
    category_breakdown: List[Any]


class ApiKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class ApiKeyCreateResponse(BaseModel):
    id: int
    name: str
    key: str
    key_prefix: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None


class ApiKeyRotateResponse(BaseModel):
    id: int
    name: str
    key: str
    key_prefix: str
    is_active: bool
    rotated_at: datetime
    expires_at: Optional[datetime] = None


# Search-related schemas
class SearchSuggestion(BaseModel):
    suggestion: str
    product_count: int


class AutocompleteSuggestion(BaseModel):
    suggestion: str
    product_count: int


class FacetBucket(BaseModel):
    value: str
    count: int


class PriceFacetBucket(BaseModel):
    range: str
    count: int


class RatingFacetBucket(BaseModel):
    range: str
    count: int


class ApiKeyListResponse(BaseModel):
    api_keys: List[ApiKeyResponse]
    total: int
    limit: int
    offset: int


class DeveloperSignupResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime


class DeveloperResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DeveloperMeResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    api_keys: List[ApiKeyResponse]
    total_api_keys: int


class BundleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    currency: str
    savings: Decimal
    savings_pct: float
    products: List[Any]
    total_products: int


class RecommendationsResponse(BaseModel):
    product_id: int
    recommendations: List[Any]
    total: int


class ProductAvailabilityResponse(BaseModel):
    id: int
    is_available: bool
    in_stock: Optional[bool] = None
    stock_level: Optional[str] = None
    last_checked: Optional[datetime] = None
    availability_sources: List[str]


class BulkAvailabilityResponse(BaseModel):
    results: List[Any]
    total: int
    available: int
    unavailable: int


class ProductStockResponse(BaseModel):
    id: int
    stock_level: str
    quantity: Optional[int] = None
    in_stock: bool
    last_checked: Optional[datetime] = None


class ProductURLAvailabilityResponse(BaseModel):
    url: str
    is_available: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    checked_at: datetime


class PriceComparisonResponse(BaseModel):
    product_id: int
    platform: str
    price: Decimal
    currency: str
    timestamp: datetime


class MerchantListResponse(BaseModel):
    merchants: List[Any]
    total: int


class BulkLookupResponse(BaseModel):
    results: List[Any]
    total: int
    found: int
    not_found: int
    multiple: int


class BatchProductRequest(BaseModel):
    product_ids: List[int] = Field(..., min_length=1, max_length=100, description="List of product IDs to look up (max 100)")


class BatchProductResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    found: int
    not_found: int


class BulkIdsRequest(BaseModel):
    ids: List[int] = Field(..., min_length=1, max_length=100, description="List of product IDs to look up (max 100)")


class BulkIdsResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    found: int
    not_found: int


class ProductReviewsResponse(BaseModel):
    product_id: int
    reviews: List[Any]
    total: int


class BrandListResponse(BaseModel):
    brands: List[Any]
    total: int


class SourceListResponse(BaseModel):
    sources: List[Any]
    total: int


class DeveloperUsageResponse(BaseModel):
    developer_id: int
    total_requests: int
    total_bandwidth_mb: float
    requests_today: int
    bandwidth_today_mb: float


class BulkImportResponse(BaseModel):
    imported: int
    failed: int
    errors: List[Any]


class QuestionResponse(BaseModel):
    id: int
    product_id: int
    question: str
    asked_by: str
    asked_at: datetime
    is_answered: bool
    answer: Optional[str] = None
    answered_at: Optional[datetime] = None
    answered_by: Optional[str] = None


class AnswerResponse(BaseModel):
    id: int
    question_id: int
    answer: str
    answered_by: str
    answered_at: datetime


class QuestionDetailResponse(BaseModel):
    id: int
    product_id: int
    question: str
    asked_by: str
    asked_at: datetime
    answer: Optional[str] = None
    answered_by: Optional[str] = None
    answered_at: Optional[datetime] = None
    is_helpful: int
    not_helpful: int


class QuestionListResponse(BaseModel):
    questions: List[QuestionResponse]
    total: int
    page: int
    page_size: int


# V2 Agent-Optimized Schemas
class V2ProductResponse(BaseModel):
    id: int
    sku: str
    source: str
    merchant_id: str
    name: str
    description: Optional[str] = None
    price: Decimal
    currency: str
    price_sgd: Optional[Decimal] = None
    buy_url: str
    affiliate_url: Optional[str] = None
    image_url: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    category_path: Optional[List[str]] = None
    rating: Optional[Decimal] = None
    review_count: Optional[int] = None
    is_available: bool = True
    in_stock: Optional[bool] = None
    stock_level: Optional[str] = None
    last_checked: Optional[datetime] = None
    data_updated_at: Optional[datetime] = Field(None, description="Timestamp when product data was last updated")
    availability_prediction: Optional[str] = Field(None, description="Predicted availability based on historical patterns (e.g., 'likely_in_stock', 'likely_out_of_stock')")
    competitor_count: Optional[int] = Field(None, description="Number of platforms selling the same product")
    metadata: Optional[dict] = None
    updated_at: datetime
    price_trend: Optional[str] = None

    model_config = {"from_attributes": True}


class V2BatchProductResponse(BaseModel):
    """Optimized batch response for agent decision-making with minimal required fields"""
    products: List[Any]
    total: int
    found: int
    not_found: int
    # Agent-specific metadata
    cache_hit_rate: Optional[float] = None
    query_time_ms: Optional[int] = None

    model_config = {"from_attributes": True}


class V2ProductListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[V2ProductResponse]
    has_more: bool = False