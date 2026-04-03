from pydantic import BaseModel, Field
from typing import Optional, List, Any
from decimal import Decimal
from datetime import datetime


class ProductResponse(BaseModel):
    id: int
    sku: str
    source: str
    merchant_id: str
    name: str = Field(..., description="Product title")
    description: Optional[str] = None
    price: Decimal
    currency: str
    buy_url: str = Field(..., description="Direct purchase URL")
    affiliate_url: Optional[str] = Field(None, description="Tracked affiliate URL (use this to send traffic)")
    image_url: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    category_path: Optional[List[str]] = None
    rating: Optional[Decimal] = None
    is_available: bool = Field(..., description="Whether product is currently in stock and available for purchase")
    last_checked: Optional[datetime] = Field(None, description="Timestamp when availability was last checked")
    metadata: Optional[Any] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[ProductResponse]
    has_more: bool = False


class CategoryNode(BaseModel):
    name: str
    count: int
    children: List["CategoryNode"] = []


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

    model_config = {"from_attributes": True}


class CompareResponse(BaseModel):
    source_product_id: int
    source_product_name: str
    matches: List[CompareMatch]
    total_matches: int


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

    model_config = {"from_attributes": True}


class CompareMatrixEntry(BaseModel):
    source_product_id: int
    source_product_name: str
    matches: List[CompareMatch]
    total_matches: int


class CompareMatrixResponse(BaseModel):
    comparisons: List[CompareMatrixEntry]
    total_products: int


class TrendingResponse(BaseModel):
    category: Optional[str] = None
    items: List[TrendingMatch]
    total: int
