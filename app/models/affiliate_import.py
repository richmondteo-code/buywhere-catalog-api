"""SQLAlchemy models for affiliate commission batch import."""

from sqlalchemy import (
    BigInteger, Column, DateTime, Index, String, Text, func
)
from app.database import Base


class AffiliateImportJob(Base):
    __tablename__ = "affiliate_import_jobs"

    id = Column(String, primary_key=True)
    network = Column(Text, nullable=False)
    status = Column(Text, nullable=False, server_default="pending")
    total_rows = Column(BigInteger, nullable=False, server_default="0")
    rows_processed = Column(BigInteger, nullable=False, server_default="0")
    rows_succeeded = Column(BigInteger, nullable=False, server_default="0")
    rows_failed = Column(BigInteger, nullable=False, server_default="0")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
