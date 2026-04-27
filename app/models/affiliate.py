from sqlalchemy import Column, String, DateTime, BigInteger, Index, Text, Numeric, Boolean, func
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class AffiliateClick(Base):
    __tablename__ = "affiliate_clicks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, index=True)
    product_id = Column(BigInteger, nullable=False, index=True)
    merchant = Column(String, nullable=False, index=True)
    platform = Column(String, nullable=True)
    tracking_id = Column(String, nullable=True, index=True)
    api_key_id = Column(String, nullable=True, index=True)
    agent_id = Column(String, nullable=True, index=True)
    affiliate_partner = Column(String, nullable=True, index=True)
    destination_url = Column(Text, nullable=False)
    referrer = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)
    user_ip = Column(Text, nullable=True)
    country = Column(String(2), nullable=True)
    clicked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("idx_affiliate_clicks_session_product", "session_id", "product_id"),
        Index("idx_affiliate_clicks_merchant", "merchant"),
        Index("idx_affiliate_clicks_clicked_at", "clicked_at"),
        Index("idx_affiliate_clicks_api_key_id", "api_key_id"),
        Index("idx_affiliate_clicks_tracking_id", "tracking_id"),
    )


class AffiliateConversion(Base):
    __tablename__ = "affiliate_conversions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    click_id = Column(BigInteger, nullable=False, index=True)
    session_id = Column(String, nullable=False, index=True)
    product_id = Column(BigInteger, nullable=False, index=True)
    merchant = Column(String, nullable=False, index=True)
    platform = Column(String, nullable=True)
    tracking_id = Column(String, nullable=True, index=True)
    api_key_id = Column(String, nullable=True, index=True)
    agent_id = Column(String, nullable=True, index=True)
    affiliate_partner = Column(String, nullable=True, index=True)
    conversion_revenue = Column(Numeric(12, 4), nullable=True)
    currency = Column(String(3), nullable=False, default="SGD")
    conversion_type = Column(String(32), nullable=True)
    conversion_data = Column(JSONB, nullable=True)
    converted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("idx_affiliate_conversions_click_id", "click_id"),
        Index("idx_affiliate_conversions_session_id", "session_id"),
        Index("idx_affiliate_conversions_product_id", "product_id"),
        Index("idx_affiliate_conversions_merchant", "merchant"),
        Index("idx_affiliate_conversions_conversion_type", "conversion_type"),
        Index("idx_affiliate_conversions_converted_at", "converted_at"),
        Index("idx_affiliate_conversions_api_key_id", "api_key_id"),
    )