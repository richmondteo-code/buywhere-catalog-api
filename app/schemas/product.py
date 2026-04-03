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
    category: Optional[str] = None
    category_path: Optional[List[str]] = None
    availability: bool = Field(..., description="Whether product is currently active/available")
    metadata: Optional[Any] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[ProductResponse]


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
