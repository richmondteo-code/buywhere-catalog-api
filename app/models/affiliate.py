from datetime import datetime
from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Numeric, String, Text, func, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class AffiliateCommission(Base):
    __tablename__ = "affiliate_commissions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    click_id = Column(Text, nullable=False, unique=True)
    conversion_id = Column(Text, nullable=True)
    product_id = Column(BigInteger, nullable=True)
    network = Column(Text, nullable=False)
    network_product_id = Column(Text, nullable=False)
    buywhere_product_id = Column(BigInteger, nullable=True)
    commission_amount = Column(Numeric(12, 2), nullable=False)
    commission_currency = Column(String(3), nullable=False)
    commission_amount_sgd = Column(Numeric(12, 2), nullable=True)
    order_value = Column(Numeric(12, 2), nullable=True)
    order_currency = Column(String(3), nullable=True)
    order_value_sgd = Column(Numeric(12, 2), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    earned_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(Text, nullable=False, default="pending")
    status_history = Column(JSONB, nullable=False, default=list)
    import_job_id = Column(String, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_ac_network", "network"),
        Index("idx_ac_status", "status"),
        Index("idx_ac_timestamp", "timestamp"),
        Index("idx_ac_import_job_id", "import_job_id"),
        Index("idx_ac_network_timestamp", "network", "timestamp"),
        Index("idx_aff_comm_network_product_id", "network_product_id"),
        Index("idx_aff_comm_buywhere_product_id", "buywhere_product_id"),
        Index("idx_aff_comm_earned_at", "earned_at"),
        Index("idx_aff_comm_updated_at", "updated_at"),
    )


class AffiliateProductMapping(Base):
    __tablename__ = "affiliate_product_mappings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    network = Column(Text, nullable=False)
    network_product_id = Column(Text, nullable=False)
    buywhere_product_id = Column(BigInteger, nullable=False)
    confidence = Column(Text, nullable=False, default="exact")
    mapped_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("network", "network_product_id", name="affiliate_product_mappings_network_sku_unique"),
        Index("idx_aff_map_network", "network"),
        Index("idx_aff_map_product_id", "buywhere_product_id"),
    )


class AffiliateNetwork(Base):
    __tablename__ = "affiliate_networks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    display_name = Column(Text, nullable=True)
    webhook_secret_encrypted = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class AffiliateRateTable(Base):
    __tablename__ = "affiliate_rate_tables"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    network = Column(Text, nullable=False)
    category = Column(Text, nullable=False, default="default")
    rate = Column(Numeric(5, 4), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_aff_rate_network", "network"),
        Index("idx_aff_rate_network_category", "network", "category"),
    )
