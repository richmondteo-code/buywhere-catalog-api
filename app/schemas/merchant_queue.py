from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


class MerchantQueueStatus(str, Enum):
    pending = "pending"
    assigned = "assigned"
    in_progress = "in_progress"
    done = "done"
    failed = "failed"


class MerchantQueueCreate(BaseModel):
    domain: str = Field(..., min_length=1, max_length=512)
    platform: str = Field(default="shopify", max_length=64)
    vertical: Optional[str] = Field(default=None, max_length=64)
    country: str = Field(default="US", min_length=2, max_length=2)
    discovered_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class MerchantQueueUpdate(BaseModel):
    status: Optional[MerchantQueueStatus] = None
    assigned_agent: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    validated_at: Optional[datetime] = None


class MerchantQueueClaim(BaseModel):
    agent: str = Field(..., min_length=1, max_length=128)


class MerchantQueueResponse(BaseModel):
    id: int
    domain: str
    platform: str
    vertical: Optional[str] = None
    country: str
    status: str
    assigned_agent: Optional[str] = None
    discovered_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None
    error_message: Optional[str] = None
    attempt_count: int = 0
    metadata: Optional[Dict[str, Any]] = None
    claimed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MerchantQueueList(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[MerchantQueueResponse]
