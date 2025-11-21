"""Global exception handlers for FastAPI application."""

import time
import traceback
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
import httpx

from .exceptions import (
    AsterDEXTradingAPIError,
    ValidationError,
    AuthenticationError,
    ResourceNotFoundError,
    RateLimitExceededError,
    ExternalAPIError,
    TimeoutError as CustomTimeoutError,
)
from .client.asterdex_client import (
    AsterDEXClientError,
    RateLimitError,
    ServerError
)
from .services.trading_service import (
    TradingServiceError,
    PositionNotFoundError,
    InvalidParameterError
)
from .logging_config import get_logger


logger = get_logger(__name__)


def create_error_response(
    status_code: int,
    error: str,
    detail: str,
    error_code: str = None,
    original_error_code: int = None,
    original_error_message: str = None,
    request_id: str = None
) -> JSONResponse:
    """
    Create standardized error response.
    
    Args:
        status_code: HTTP status code
        error: Error type/category
        detail: Detailed error message
        error_code: Application-specific error code
        original_error_code: Original error code from external API
        original_error_message: Original error message from external API
        request_id: Request ID for tracking
        
    Returns:
        JSONResponse with error details
    """
    content = {
        "error": error,
        "detail": detail,
        "code": error_code or status_code,
        "timestamp": int(time.time() * 1000)
    }
    
    if original_error_code is not None:
        content["original_error_code"] = original_error_code
    
    if original_error_message:
        content["original_error_message"] = original_error_message
    
    if request_id:
        content["request_id"] = request_id
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )


async def asterdex_trading_api_error_handler(
    request: Request,
    exc: AsterDEXTradingAPIError
) -> JSONResponse:
    """
    Handle custom AsterDEX Trading API errors.
    
    Args:
        request: FastAPI request
        exc: Custom exception
        
    Returns:
        JSONResponse with error details
    """
    logger.error(
        "application_error",
        error_type=exc.__class__.__name__,
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        path=request.url.path,
        details=exc.details
    )
    
    response_content = {
        "error": exc.__class__.__name__,
        "detail": exc.message,
        "code": exc.error_code or exc.status_code,
        "timestamp": int(time.time() * 1000)
    }
    
    # Add additional details if present
    if exc.details:
        response_content.update(exc.details)
    
    # Add retry_after header for rate limit errors
    headers = {}
    if isinstance(exc, RateLimitExceededError) and exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_content,
        headers=headers if headers else None
    )


async def asterdex_client_error_handler(
    request: Request,
    exc: AsterDEXClientError
) -> JSONResponse:
    """
    Handle AsterDEX client errors.
    
    Maps client errors to appropriate HTTP status codes and formats
    error responses with original AsterDEX error information.
    
    Args:
        request: FastAPI request
        exc: AsterDEX client exception
        
    Returns:
        JSONResponse with error details
    """
    # Determine status code based on exception type
    if isinstance(exc, RateLimitError):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
        error_type = "RateLimitError"
    elif isinstance(exc, ServerError):
        status_code = status.HTTP_502_BAD_GATEWAY
        error_type = "ServerError"
    else:
        status_code = status.HTTP_502_BAD_GATEWAY
        error_type = "AsterDEXClientError"
    
    # Try to extract original error details from exception message
    error_message = str(exc)
    original_error_code = None
    original_error_message = None
    
    # Parse error message if it contains structured error info
    if "Client error" in error_message and ":" in error_message:
        try:
            # Extract status code and error details
            parts = error_message.split(":", 1)
            if len(parts) > 1:
                original_error_message = parts[1].strip()
        except Exception:
            pass
    
    logger.error(
        "asterdex_client_error",
        error_type=error_type,
        message=error_message,
        status_code=status_code,
        path=request.url.path
    )
    
    return create_error_response(
        status_code=status_code,
        error=error_type,
        detail=f"AsterDEX API error: {error_message}",
        error_code=error_type.upper(),
        original_error_message=original_error_message
    )


async def trading_service_error_handler(
    request: Request,
    exc: TradingServiceError
) -> JSONResponse:
    """
    Handle trading service errors.
    
    Args:
        request: FastAPI request
        exc: Trading service exception
        
    Returns:
        JSONResponse with error details
    """
    # Determine status code based on exception type
    if isinstance(exc, PositionNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
        error_type = "PositionNotFound"
    elif isinstance(exc, InvalidParameterError):
        status_code = status.HTTP_400_BAD_REQUEST
        error_type = "InvalidParameter"
    else:
        status_code = status.HTTP_400_BAD_REQUEST
        error_type = "TradingServiceError"
    
    logger.error(
        "trading_service_error",
        error_type=error_type,
        message=str(exc),
        status_code=status_code,
        path=request.url.path
    )
    
    return create_error_response(
        status_code=status_code,
        error=error_type,
        detail=str(exc),
        error_code=error_type.upper()
    )


async def validation_error_handler(
    request: Request,
    exc: Union[RequestValidationError, PydanticValidationError]
) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Args:
        request: FastAPI request
        exc: Validation exception
        
    Returns:
        JSONResponse with validation error details
    """
    errors = []
    
    # Extract validation errors
    if hasattr(exc, 'errors'):
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error.get("loc", []))
            message = error.get("msg", "Validation error")
            error_type = error.get("type", "value_error")
            
            errors.append({
                "field": field,
                "message": message,
                "type": error_type
            })
    
    logger.warning(
        "validation_error",
        path=request.url.path,
        errors=errors
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "ValidationError",
            "detail": "Request validation failed",
            "code": "VALIDATION_ERROR",
            "timestamp": int(time.time() * 1000),
            "validation_errors": errors
        }
    )


async def httpx_timeout_handler(
    request: Request,
    exc: httpx.TimeoutException
) -> JSONResponse:
    """
    Handle httpx timeout errors.
    
    Args:
        request: FastAPI request
        exc: Timeout exception
        
    Returns:
        JSONResponse with timeout error details
    """
    logger.error(
        "request_timeout",
        path=request.url.path,
        error=str(exc)
    )
    
    return create_error_response(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        error="TimeoutError",
        detail="Request to AsterDEX API timed out. Please try again.",
        error_code="TIMEOUT_ERROR"
    )


async def httpx_error_handler(
    request: Request,
    exc: httpx.HTTPError
) -> JSONResponse:
    """
    Handle general httpx HTTP errors.
    
    Args:
        request: FastAPI request
        exc: HTTP exception
        
    Returns:
        JSONResponse with error details
    """
    logger.error(
        "http_error",
        path=request.url.path,
        error=str(exc),
        error_type=exc.__class__.__name__
    )
    
    return create_error_response(
        status_code=status.HTTP_502_BAD_GATEWAY,
        error="HTTPError",
        detail=f"HTTP error occurred: {str(exc)}",
        error_code="HTTP_ERROR"
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle unexpected exceptions.
    
    Args:
        request: FastAPI request
        exc: Exception
        
    Returns:
        JSONResponse with error details
    """
    # Get full traceback
    tb = traceback.format_exc()
    
    logger.error(
        "unexpected_error",
        path=request.url.path,
        error=str(exc),
        error_type=exc.__class__.__name__,
        traceback=tb
    )
    
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error="InternalServerError",
        detail="An unexpected error occurred. Please try again later.",
        error_code="INTERNAL_SERVER_ERROR"
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Custom application errors
    app.add_exception_handler(
        AsterDEXTradingAPIError,
        asterdex_trading_api_error_handler
    )
    
    # AsterDEX client errors
    app.add_exception_handler(
        AsterDEXClientError,
        asterdex_client_error_handler
    )
    
    # Trading service errors
    app.add_exception_handler(
        TradingServiceError,
        trading_service_error_handler
    )
    
    # Validation errors
    app.add_exception_handler(
        RequestValidationError,
        validation_error_handler
    )
    app.add_exception_handler(
        PydanticValidationError,
        validation_error_handler
    )
    
    # HTTP client errors
    app.add_exception_handler(
        httpx.TimeoutException,
        httpx_timeout_handler
    )
    app.add_exception_handler(
        httpx.HTTPError,
        httpx_error_handler
    )
    
    # Generic exception handler (catch-all)
    app.add_exception_handler(
        Exception,
        generic_exception_handler
    )
    
    logger.info("exception_handlers_registered")
