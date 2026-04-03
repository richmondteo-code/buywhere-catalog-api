import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.product import ApiKey

settings = get_settings()
bearer_scheme = HTTPBearer()


def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_api_key() -> tuple[str, str]:
    """Returns (raw_key, key_hash). Store hash, give raw to developer."""
    raw = "bw_" + secrets.token_urlsafe(32)
    return raw, hash_key(raw)


def create_access_token(data: dict) -> str:
    return jwt.encode(data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


async def get_current_api_key(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    token = credentials.credentials

    # Try JWT decode first
    payload = decode_access_token(token)
    if payload and "key_id" in payload:
        key_id = payload["key_id"]
        result = await db.execute(
            select(ApiKey).where(ApiKey.id == key_id, ApiKey.is_active == True)
        )
        api_key = result.scalar_one_or_none()
    else:
        # Fall back to raw key hash lookup (for direct bw_ keys)
        key_hash = hash_key(token)
        result = await db.execute(
            select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
        )
        api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last_used_at without blocking response
    await db.execute(
        update(ApiKey)
        .where(ApiKey.id == api_key.id)
        .values(last_used_at=datetime.now(timezone.utc))
    )

    return api_key


async def provision_api_key(
    developer_id: str,
    name: str,
    tier: str = "basic",
    db: AsyncSession = None,
) -> tuple[str, ApiKey]:
    """Create a new API key. Returns (raw_key, ApiKey record)."""
    raw_key, key_hash = generate_api_key()
    key_id = str(uuid.uuid4())

    api_key = ApiKey(
        id=key_id,
        key_hash=key_hash,
        developer_id=developer_id,
        name=name,
        tier=tier,
        is_active=True,
    )
    db.add(api_key)
    await db.flush()

    return raw_key, api_key
