from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from app.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key: str = Security(api_key_header)) -> str:
    settings = get_settings()
    if not settings.auth_enabled:
        return ""
    if api_key in settings.api_keys:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
    )
