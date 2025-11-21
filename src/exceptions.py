"""Custom exception classes for the AsterDEX Trading API."""

from typing import Optional, Dict, Any


class AsterDEXTradingAPIError(Exception):
    """Base exception for all AsterDEX Trading API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base exception.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code
            error_code: Application-specific error code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class ValidationError(AsterDEXTradingAPIError):
    """Raised when request validation fails."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code=error_code,
            details=details
        )


class AuthenticationError(AsterDEXTradingAPIError):
    """Raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: str = "AUTHENTICATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=401,
            error_code=error_code,
            details=details
        )


class ResourceNotFoundError(AsterDEXTradingAPIError):
    """Raised when a requested resource is not found."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "RESOURCE_NOT_FOUND",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=404,
            error_code=error_code,
            details=details
        )


class RateLimitExceededError(AsterDEXTradingAPIError):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        error_code: str = "RATE_LIMIT_EXCEEDED",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            status_code=429,
            error_code=error_code,
            details=details
        )
        self.retry_after = retry_after


class ExternalAPIError(AsterDEXTradingAPIError):
    """Raised when external API (AsterDEX) returns an error."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 502,
        error_code: str = "EXTERNAL_API_ERROR",
        original_error_code: Optional[int] = None,
        original_error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if original_error_code:
            details["original_error_code"] = original_error_code
        if original_error_message:
            details["original_error_message"] = original_error_message
        
        super().__init__(
            message=message,
            status_code=status_code,
            error_code=error_code,
            details=details
        )
        self.original_error_code = original_error_code
        self.original_error_message = original_error_message


class TimeoutError(AsterDEXTradingAPIError):
    """Raised when a request times out."""
    
    def __init__(
        self,
        message: str = "Request timeout",
        error_code: str = "TIMEOUT_ERROR",
        timeout_seconds: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        
        super().__init__(
            message=message,
            status_code=504,
            error_code=error_code,
            details=details
        )
        self.timeout_seconds = timeout_seconds


class InsufficientBalanceError(AsterDEXTradingAPIError):
    """Raised when account has insufficient balance for operation."""
    
    def __init__(
        self,
        message: str = "Insufficient balance",
        error_code: str = "INSUFFICIENT_BALANCE",
        required_balance: Optional[str] = None,
        available_balance: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if required_balance:
            details["required_balance"] = required_balance
        if available_balance:
            details["available_balance"] = available_balance
        
        super().__init__(
            message=message,
            status_code=400,
            error_code=error_code,
            details=details
        )


class InvalidOrderError(AsterDEXTradingAPIError):
    """Raised when order parameters are invalid."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "INVALID_ORDER",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code=error_code,
            details=details
        )


class PositionError(AsterDEXTradingAPIError):
    """Raised when position operation fails."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "POSITION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code=error_code,
            details=details
        )


class ConfigurationError(AsterDEXTradingAPIError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "CONFIGURATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code=error_code,
            details=details
        )
