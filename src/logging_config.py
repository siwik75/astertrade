"""Structured logging configuration for AsterDEX Trading API."""

import re
import sys
import structlog
from typing import Any, Dict


# Sensitive data patterns to filter from logs
SENSITIVE_PATTERNS = [
    # Private keys (0x followed by 64 hex chars)
    (re.compile(r'0x[a-fA-F0-9]{64}'), '0x***PRIVATE_KEY_REDACTED***'),
    # Signatures (0x followed by 130 hex chars)
    (re.compile(r'0x[a-fA-F0-9]{130}'), '0x***SIGNATURE_REDACTED***'),
    # Generic signature field
    (re.compile(r'"signature"\s*:\s*"[^"]*"'), '"signature": "***REDACTED***"'),
    # Private key field
    (re.compile(r'"private_key"\s*:\s*"[^"]*"'), '"private_key": "***REDACTED***"'),
    (re.compile(r'"privateKey"\s*:\s*"[^"]*"'), '"privateKey": "***REDACTED***"'),
    # Webhook secret
    (re.compile(r'"webhook_secret"\s*:\s*"[^"]*"'), '"webhook_secret": "***REDACTED***"'),
    # Authorization headers
    (re.compile(r'"authorization"\s*:\s*"[^"]*"', re.IGNORECASE), '"authorization": "***REDACTED***"'),
]


def filter_sensitive_data(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter sensitive data from log events.
    
    This processor removes or masks sensitive information like private keys,
    signatures, and secrets from log output to prevent accidental exposure.
    
    Args:
        logger: The logger instance
        method_name: The logging method name
        event_dict: The log event dictionary
        
    Returns:
        Modified event dictionary with sensitive data filtered
    """
    # Convert event dict to string for pattern matching
    event_str = str(event_dict)
    
    # Apply all sensitive patterns
    for pattern, replacement in SENSITIVE_PATTERNS:
        event_str = pattern.sub(replacement, event_str)
    
    # Also filter specific keys in the event dict
    sensitive_keys = [
        'private_key', 'privateKey', 'asterdex_private_key',
        'signature', 'webhook_secret', 'password', 'token',
        'authorization', 'api_key', 'apiKey'
    ]
    
    for key in sensitive_keys:
        if key in event_dict:
            event_dict[key] = '***REDACTED***'
    
    # Recursively filter nested dictionaries
    for key, value in event_dict.items():
        if isinstance(value, dict):
            event_dict[key] = _filter_dict_recursive(value, sensitive_keys)
        elif isinstance(value, str):
            # Apply pattern matching to string values
            for pattern, replacement in SENSITIVE_PATTERNS:
                value = pattern.sub(replacement, value)
            event_dict[key] = value
    
    return event_dict


def _filter_dict_recursive(data: Dict[str, Any], sensitive_keys: list) -> Dict[str, Any]:
    """
    Recursively filter sensitive data from nested dictionaries.
    
    Args:
        data: Dictionary to filter
        sensitive_keys: List of sensitive key names
        
    Returns:
        Filtered dictionary
    """
    filtered = {}
    for key, value in data.items():
        if key in sensitive_keys:
            filtered[key] = '***REDACTED***'
        elif isinstance(value, dict):
            filtered[key] = _filter_dict_recursive(value, sensitive_keys)
        elif isinstance(value, str):
            # Apply pattern matching to string values
            for pattern, replacement in SENSITIVE_PATTERNS:
                value = pattern.sub(replacement, value)
            filtered[key] = value
        else:
            filtered[key] = value
    return filtered


def add_app_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add application context to log events.
    
    This processor adds consistent context information to all log events
    including the application name and environment.
    
    Args:
        logger: The logger instance
        method_name: The logging method name
        event_dict: The log event dictionary
        
    Returns:
        Modified event dictionary with app context
    """
    event_dict['app'] = 'asterdex-trading-api'
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging with JSON formatter.
    
    Sets up structlog with the following features:
    - JSON output for machine-readable logs
    - ISO timestamp format
    - Log level filtering
    - Context processors for timestamp, log level, logger name
    - Sensitive data filtering
    - Stack trace rendering
    - Exception info formatting
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Normalize log level
    log_level = log_level.upper()
    
    # Configure structlog processors
    processors = [
        # Add contextvars (for request context, etc.)
        structlog.contextvars.merge_contextvars,
        # Add application context
        add_app_context,
        # Add log level
        structlog.processors.add_log_level,
        # Add logger name
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        # Add timestamp in ISO format
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        # Render stack info if present
        structlog.processors.StackInfoRenderer(),
        # Format exception info
        structlog.processors.format_exc_info,
        # Filter sensitive data (must be before JSONRenderer)
        filter_sensitive_data,
        # Render as JSON
        structlog.processors.JSONRenderer()
    ]
    
    # Map log level string to logging level constant
    import logging
    log_level_int = getattr(logging, log_level, logging.INFO)
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level_int),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)
