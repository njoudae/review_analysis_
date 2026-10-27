import secrets

from fastapi import Header, HTTPException, status

from .config import settings


def require_api_key(x_api_key: str = Header(default="")) -> None:
    if settings.environment == "test":
        return
    if not x_api_key or not secrets.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

