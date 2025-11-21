"""Tests for configuration module"""

import pytest
from pydantic import ValidationError
from src.config import Settings


def test_settings_validation_valid_addresses():
    """Test that valid Ethereum addresses are accepted"""
    settings = Settings(
        asterdex_user_address="0x1234567890123456789012345678901234567890",
        asterdex_signer_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
        asterdex_private_key="0x" + "a" * 64
    )
    assert settings.asterdex_user_address == "0x1234567890123456789012345678901234567890"
    assert settings.asterdex_signer_address == "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"


def test_settings_validation_invalid_address():
    """Test that invalid Ethereum addresses are rejected"""
    with pytest.raises(ValidationError):
        Settings(
            asterdex_user_address="invalid_address",
            asterdex_signer_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            asterdex_private_key="0x" + "a" * 64
        )


def test_settings_validation_invalid_private_key():
    """Test that invalid private keys are rejected"""
    with pytest.raises(ValidationError):
        Settings(
            asterdex_user_address="0x1234567890123456789012345678901234567890",
            asterdex_signer_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            asterdex_private_key="invalid_key"
        )


def test_settings_default_values():
    """Test that default values are set correctly"""
    settings = Settings(
        asterdex_user_address="0x1234567890123456789012345678901234567890",
        asterdex_signer_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
        asterdex_private_key="0x" + "a" * 64
    )
    assert settings.asterdex_base_url == "https://fapi.asterdex.com"
    assert settings.server_host == "0.0.0.0"
    assert settings.server_port == 8000
    assert settings.default_leverage == 10
    assert settings.default_margin_type == "CROSSED"
    assert settings.request_timeout == 30
    assert settings.max_retries == 3
    assert settings.log_level == "INFO"


def test_settings_webhook_secret_configured():
    """Test webhook secret configuration check"""
    settings = Settings(
        asterdex_user_address="0x1234567890123456789012345678901234567890",
        asterdex_signer_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
        asterdex_private_key="0x" + "a" * 64
    )
    assert not settings.is_webhook_secret_configured()
    
    settings.webhook_secret = "my_secret"
    assert settings.is_webhook_secret_configured()


def test_settings_safe_config():
    """Test that sensitive data is masked in safe config"""
    settings = Settings(
        asterdex_user_address="0x1234567890123456789012345678901234567890",
        asterdex_signer_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
        asterdex_private_key="0x" + "a" * 64,
        webhook_secret="my_secret"
    )
    safe_config = settings.get_safe_config()
    assert safe_config["asterdex_private_key"] == "***REDACTED***"
    assert safe_config["webhook_secret"] == "***REDACTED***"
    assert safe_config["asterdex_user_address"] == "0x1234567890123456789012345678901234567890"
