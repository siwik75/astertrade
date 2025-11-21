"""Health check and root endpoints."""

import time
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse

from ..config import get_settings
from ..logging_config import get_logger


logger = get_logger(__name__)
router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health Check",
    description="Verify service availability and configuration status for monitoring and load balancers.",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": 1699999999999,
                        "version": "1.0.0",
                        "configuration": {
                            "base_url": "https://fapi.asterdex.com",
                            "webhook_secret_configured": True,
                            "default_leverage": 10,
                            "default_margin_type": "CROSSED"
                        }
                    }
                }
            }
        },
        503: {
            "description": "Service unavailable or misconfigured",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Service Unavailable",
                        "detail": "Configuration error: User address not configured",
                        "code": 503
                    }
                }
            }
        }
    }
)
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns the current health status of the service, including:
    - Service status
    - Current timestamp
    - API version
    - Configuration validation status
    
    This endpoint can be used by load balancers, monitoring systems,
    and orchestration platforms to verify service availability.
    
    Returns:
        Health status information
        
    Raises:
        HTTPException: If configuration validation fails
    """
    logger.debug("health_check_requested")
    
    try:
        # Validate configuration is loaded
        settings = get_settings()
        
        # Verify critical configuration is present
        if not settings.asterdex_user_address:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Configuration error: User address not configured"
            )
        
        if not settings.asterdex_signer_address:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Configuration error: Signer address not configured"
            )
        
        if not settings.asterdex_private_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Configuration error: Private key not configured"
            )
        
        response = {
            "status": "healthy",
            "timestamp": int(time.time() * 1000),
            "version": "1.0.0",
            "configuration": {
                "base_url": settings.asterdex_base_url,
                "webhook_secret_configured": settings.is_webhook_secret_configured(),
                "default_leverage": settings.default_leverage,
                "default_margin_type": settings.default_margin_type
            }
        }
        
        logger.debug("health_check_passed")
        
        return response
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(
            "health_check_failed",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )


@router.get(
    "/",
    summary="Root Endpoint",
    description="Redirects to interactive API documentation.",
    responses={
        307: {
            "description": "Redirect to /docs"
        }
    }
)
async def root() -> RedirectResponse:
    """
    Root endpoint.
    
    Redirects to the interactive API documentation at /docs.
    This provides a convenient entry point for users accessing
    the API root URL.
    
    Returns:
        Redirect response to /docs
    """
    logger.debug("root_endpoint_accessed")
    return RedirectResponse(url="/docs")
