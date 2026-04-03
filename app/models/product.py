from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Numeric, String, Text,
    func, UniqueConstraint, Integer, ARRAY, Index
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from app.database import Base


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    source = Column(String, nullable=False)
    country = Column(String(2), nullable=False, default="SG")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Product(Base):
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    canonical_id = Column(BigInteger, nullable=True, index=True)
    sku = Column(Text, nullable=False)
    source = Column(Text, nullable=False)
    merchant_id = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="SGD")
    url = Column(Text, nullable=False)
    brand = Column(Text)
    category = Column(Text)
    category_path = Column(ARRAY(Text))
    image_url = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    is_available = Column(Boolean, nullable=False, default=True)
    last_checked = Column(DateTime(timezone=True), nullable=True)
    rating = Column(Numeric(3, 2), nullable=True)
    metadata_ = Column("metadata", JSONB)
    title_search_vector = Column(TSVECTOR)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("sku", "source", name="products_sku_source_unique"),
        Index("idx_products_canonical", "canonical_id"),
        Index("idx_products_is_active", "is_active"),
        Index("idx_products_source", "source"),
        Index("idx_products_url", "url"),
        Index("idx_products_title", "title"),
        Index("idx_products_price", "price"),
        Index("idx_products_merchant_id", "merchant_id"),
        Index("idx_products_brand", "brand"),
    )


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source = Column(Text, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at = Column(DateTime(timezone=True))
    rows_inserted = Column(Integer)
    rows_updated = Column(Integer)
    rows_failed = Column(Integer)
    status = Column(Text, nullable=False, default="running")
    error_message = Column(Text)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True)
    key_hash = Column(String, nullable=False, unique=True)
    developer_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    tier = Column(String, nullable=False, default="basic")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True))


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="SGD")
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_price_history_product_recorded", "product_id", "recorded_at"),
    )


class Click(Base):
    __tablename__ = "clicks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tracking_id = Column(Text, nullable=False, unique=True)
    product_id = Column(BigInteger, nullable=False)
    platform = Column(Text, nullable=False)
    destination_url = Column(Text, nullable=False)
    api_key_id = Column(Text, nullable=True)
    clicked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_clicks_tracking_id", "tracking_id"),
        Index("idx_clicks_product_id", "product_id"),
        Index("idx_clicks_clicked_at", "clicked_at"),
    )