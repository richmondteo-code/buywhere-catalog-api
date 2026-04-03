from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class PlatformProductCount(BaseModel):
    source: str
    product_count: int
    last_updated: Optional[datetime] = None


class IngestionRunInfo(BaseModel):
    source: Optional[str] = None
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    last_rows_inserted: Optional[int] = None
    last_rows_updated: Optional[int] = None


class CatalogStatus(BaseModel):
    total_unique_products: int
    platforms: List[PlatformProductCount]
    ingestion_runs: List[IngestionRunInfo]
    goal_million: float = 1.0
    progress_percent: float


class PlatformCompliance(BaseModel):
    source: str
    total: int
    compliant: int
    compliance_rate: float


class SchemaComplianceReport(BaseModel):
    total_products: int
    compliant_products: int
    compliance_rate: float
    by_platform: List[PlatformCompliance]
    missing_title: int
    missing_price: int
    missing_source: int
    missing_source_id: int
    missing_url: int
    incomplete_products: int


class DuplicateGroup(BaseModel):
    canonical_id: int
    product_ids: List[int]
    source_count: int
    sources: List[str]
    sample_title: str
    price_min: Decimal
    price_max: Decimal


class DeduplicationReport(BaseModel):
    total_products: int
    products_with_canonical: int
    duplicate_rate: float
    duplicate_groups: int
    sample_duplicates: List[DuplicateGroup]


class StaleProductInfo(BaseModel):
    product_id: int
    title: str
    source: str
    last_updated: datetime
    days_stale: int


class FreshnessReport(BaseModel):
    total_products: int
    stale_products: int
    stale_rate: float
    re_scrape_count: int
    by_platform: dict[str, int]
    sample_stale: List[StaleProductInfo]


class CatalogHealthReport(BaseModel):
    generated_at: datetime
    total_indexed: int
    by_platform: dict[str, int]
    compliance: SchemaComplianceReport
    deduplication: DeduplicationReport
    freshness: FreshnessReport


class ScraperHealth(BaseModel):
    source: str
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    last_rows_inserted: Optional[int] = None
    last_rows_updated: Optional[int] = None
    last_rows_failed: Optional[int] = None
    product_count: int = 0
    is_healthy: bool = False
    hours_since_last_run: Optional[float] = None
    error_message: Optional[str] = None


class ScraperHealthReport(BaseModel):
    generated_at: datetime
    scrapers: List[ScraperHealth]
    total_scrapers: int
    healthy_count: int
    unhealthy_count: int


class CatalogStatsReport(BaseModel):
    generated_at: datetime
    total_products: int
    by_platform: dict[str, int]
    by_category: dict[str, int]