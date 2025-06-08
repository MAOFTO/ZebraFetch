from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from typing import Optional

from ..config import get_settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(
    api_key_header: Optional[str] = Security(API_KEY_HEADER),
) -> str:
    """Validate API key from header."""
    settings = get_settings()

    if not settings.auth_enabled:
        return "disabled"

    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )

    if api_key_header not in settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    return api_key_header
