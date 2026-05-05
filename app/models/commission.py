from datetime import date
from sqlalchemy import BigInteger, Column, Date, DateTime, Numeric, Text, func, Index, UniqueConstraint
from app.database import Base


class CommissionDaily(Base):
    __tablename__ = "commission_daily"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    network = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="approved")

    commission_count = Column(BigInteger, nullable=False, default=0)
    commission_amount_sgd = Column(Numeric(14, 2), nullable=False, default=0)
    order_value_sgd = Column(Numeric(14, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("date", "network", "status", name="uq_commission_daily_date_network_status"),
        Index("idx_commission_daily_date", "date"),
        Index("idx_commission_daily_network", "network"),
        Index("idx_commission_daily_date_network", "date", "network"),
    )
