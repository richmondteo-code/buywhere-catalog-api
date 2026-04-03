from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://buywhere:buywhere@localhost:5432/catalog"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 365  # 1 year for API keys

    # Rate limiting
    rate_limit_per_minute: int = 1000
    redis_url: str = "redis://localhost:6379/0"

    # App
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "production"

    model_config = {"env_file": ".env", "case_sensitive": False}


@lru_cache
def get_settings() -> Settings:
    return Settings()
