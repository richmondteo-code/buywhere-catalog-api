from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Numeric, String, Text,
    func, UniqueConstraint, Integer, ARRAY
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
    sku = Column(Text, nullable=False)
    source = Column(Text, nullable=False)
    merchant_id = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="SGD")
    url = Column(Text, nullable=False)
    category = Column(Text)
    category_path = Column(ARRAY(Text))
    image_url = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    metadata_ = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("sku", "source", name="products_sku_source_unique"),
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
