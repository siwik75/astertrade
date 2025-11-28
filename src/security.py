"""Security and authentication utilities."""

import secrets
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import APIKeyHeader
from .config import get_settings
from .logging_config import get_logger

logger = get_logger(__name__)

# API Key header scheme
# This will automatically show in OpenAPI docs
api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="API key for accessing protected endpoints. Generate with: python generate_api_key.py"
)


def verify_api_key(api_key: Optional[str] = Depends(api_key_header)) -> str:
    """
    Verify API key from request header.
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        The verified API key
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    settings = get_settings()
    
    # Check if API key authentication is enabled
    if not settings.api_key:
        logger.warning("api_key_not_configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key authentication is not configured on the server"
        )
    
    # Check if API key was provided
    if not api_key:
        logger.warning("api_key_missing")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is required. Provide it in the X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Verify API key using constant-time comparison
    if not secrets.compare_digest(api_key, settings.api_key):
        logger.warning("api_key_invalid", provided_key_prefix=api_key[:8] if len(api_key) >= 8 else "***")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    logger.debug("api_key_verified")
    return api_key


def generate_api_key(length: int = 32) -> str:
    """
    Generate a secure random API key.
    
    Args:
        length: Length of the API key in bytes (default 32)
        
    Returns:
        Hex-encoded API key string
    """
    return secrets.token_hex(length)
