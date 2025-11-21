"""Tests for structured logging configuration."""

import json
import pytest
from io import StringIO
import sys

from src.logging_config import (
    configure_logging,
    get_logger,
    filter_sensitive_data,
    _filter_dict_recursive
)


def test_configure_logging():
    """Test that logging configuration works without errors."""
    # Should not raise any exceptions
    configure_logging("INFO")
    configure_logging("DEBUG")
    configure_logging("WARNING")
    configure_logging("ERROR")


def test_get_logger():
    """Test that get_logger returns a valid logger instance."""
    configure_logging("INFO")
    logger = get_logger("test_module")
    
    assert logger is not None
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")
    assert hasattr(logger, "warning")
    assert hasattr(logger, "debug")


def test_filter_sensitive_data_private_key():
    """Test that private keys are filtered from logs."""
    event_dict = {
        "message": "test",
        "private_key": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "other_data": "visible"
    }
    
    filtered = filter_sensitive_data(None, "info", event_dict)
    
    assert filtered["private_key"] == "***REDACTED***"
    assert filtered["other_data"] == "visible"


def test_filter_sensitive_data_signature():
    """Test that signatures are filtered from logs."""
    event_dict = {
        "message": "test",
        "signature": "0x" + "a" * 130,
        "other_data": "visible"
    }
    
    filtered = filter_sensitive_data(None, "info", event_dict)
    
    assert filtered["signature"] == "***REDACTED***"
    assert filtered["other_data"] == "visible"


def test_filter_sensitive_data_webhook_secret():
    """Test that webhook secrets are filtered from logs."""
    event_dict = {
        "message": "test",
        "webhook_secret": "my-secret-token",
        "other_data": "visible"
    }
    
    filtered = filter_sensitive_data(None, "info", event_dict)
    
    assert filtered["webhook_secret"] == "***REDACTED***"
    assert filtered["other_data"] == "visible"


def test_filter_sensitive_data_nested():
    """Test that sensitive data in nested dicts is filtered."""
    event_dict = {
        "message": "test",
        "config": {
            "private_key": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "public_data": "visible"
        }
    }
    
    filtered = filter_sensitive_data(None, "info", event_dict)
    
    assert filtered["config"]["private_key"] == "***REDACTED***"
    assert filtered["config"]["public_data"] == "visible"


def test_filter_dict_recursive():
    """Test recursive dictionary filtering."""
    sensitive_keys = ["private_key", "signature", "webhook_secret"]
    
    data = {
        "level1": {
            "private_key": "secret",
            "level2": {
                "signature": "secret",
                "public": "visible"
            }
        },
        "webhook_secret": "secret",
        "public_data": "visible"
    }
    
    filtered = _filter_dict_recursive(data, sensitive_keys)
    
    assert filtered["level1"]["private_key"] == "***REDACTED***"
    assert filtered["level1"]["level2"]["signature"] == "***REDACTED***"
    assert filtered["level1"]["level2"]["public"] == "visible"
    assert filtered["webhook_secret"] == "***REDACTED***"
    assert filtered["public_data"] == "visible"


def test_filter_sensitive_data_in_strings():
    """Test that sensitive patterns in string values are filtered."""
    event_dict = {
        "message": "Private key is 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "other": "normal text"
    }
    
    filtered = filter_sensitive_data(None, "info", event_dict)
    
    assert "0x1234567890abcdef" not in filtered["message"]
    assert "***PRIVATE_KEY_REDACTED***" in filtered["message"]
    assert filtered["other"] == "normal text"


def test_logging_output_is_json():
    """Test that logging output is valid JSON."""
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        configure_logging("INFO")
        logger = get_logger("test")
        
        # Log a message
        logger.info("test_message", key="value")
        
        # Get output
        output = sys.stdout.getvalue()
        
        # Should be valid JSON
        if output.strip():
            log_entry = json.loads(output.strip())
            assert "event" in log_entry or "message" in log_entry
    
    finally:
        sys.stdout = old_stdout


def test_app_context_added():
    """Test that app context is added to log events."""
    from src.logging_config import add_app_context
    
    event_dict = {"message": "test"}
    result = add_app_context(None, None, event_dict)
    
    assert result["app"] == "asterdex-trading-api"
    assert result["message"] == "test"
