from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from app.models.product import ApiKey


def get_key_identifier(request: Request) -> str:
    """Use API key id for rate limiting when available, else IP."""
    api_key: ApiKey | None = getattr(request.state, "api_key", None)
    if api_key:
        return f"key:{api_key.id}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=get_key_identifier)
