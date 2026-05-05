from sqlalchemy import Column, BigInteger, String, Text, Integer, Numeric, DateTime, func, Index
from sqlalchemy.dialects.postgresql import ARRAY
from app.database import Base


class QueryLog(Base):
    __tablename__ = "query_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    api_key_id = Column(String, nullable=True)
    path = Column(Text, nullable=False)
    method = Column(String, nullable=False, server_default="GET")
    status_code = Column(Integer, nullable=False)
    duration_ms = Column(Numeric(10, 2), nullable=True)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    country = Column(String(2), nullable=True)
    agent_framework = Column(Text, nullable=True)
    mcp_tool_name = Column(Text, nullable=True)
    ai_model = Column(Text, nullable=True)
    region = Column(String(10), nullable=True)
    result_count = Column(Integer, nullable=True)
    keywords = Column(ARRAY(Text), nullable=True)
    categories = Column(ARRAY(Text), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("idx_query_log_api_key_id", "api_key_id"),
        Index("idx_query_log_created_at", "created_at"),
        Index("idx_query_log_status_code", "status_code"),
        Index("idx_query_log_agent_framework", "agent_framework"),
        Index("idx_query_log_mcp_tool", "mcp_tool_name"),
        Index("idx_query_log_ai_model", "ai_model"),
        Index("idx_query_log_region", "region"),
    )
