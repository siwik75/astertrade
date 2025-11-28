"""Configuration module for AsterDEX Trading API"""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # AsterDEX API Configuration
    asterdex_base_url: str = Field(
        default="https://fapi.asterdex.com",
        description="AsterDEX API base URL"
    )
    asterdex_user_address: str = Field(
        ...,
        description="Main wallet address registered on AsterDEX"
    )
    asterdex_signer_address: str = Field(
        ...,
        description="API wallet address used for signing requests"
    )
    asterdex_private_key: str = Field(
        ...,
        description="Private key for API wallet (keep secure!)"
    )
    
    # Server Configuration
    server_host: str = Field(
        default="0.0.0.0",
        description="Server host address"
    )
    server_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port number"
    )
    
    # Webhook Security
    webhook_secret: Optional[str] = Field(
        default=None,
        description="Optional secret token for webhook validation"
    )
    
    # API Security
    api_key: Optional[str] = Field(
        default=None,
        description="API key for securing sensitive endpoints (positions, account, orders)"
    )
    
    # Trading Defaults
    default_leverage: int = Field(
        default=10,
        ge=1,
        le=125,
        description="Default leverage for new positions"
    )
    default_margin_type: str = Field(
        default="CROSSED",
        description="Default margin type (ISOLATED or CROSSED)"
    )
    
    # API Limits and Timeouts
    request_timeout: int = Field(
        default=30,
        ge=1,
        description="HTTP request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum number of retry attempts for failed requests"
    )
    rate_limit_retry_delay: int = Field(
        default=2,
        ge=1,
        description="Base delay in seconds for rate limit retries"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    @field_validator("asterdex_user_address", "asterdex_signer_address")
    @classmethod
    def validate_ethereum_address(cls, v: str) -> str:
        """Validate Ethereum address format"""
        if not v.startswith("0x") or len(v) != 42:
            raise ValueError("Invalid Ethereum address format. Must be 0x followed by 40 hex characters")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("Invalid Ethereum address. Must contain only hexadecimal characters")
        return v.lower()
    
    @field_validator("asterdex_private_key")
    @classmethod
    def validate_private_key(cls, v: str) -> str:
        """Validate private key format"""
        if not v.startswith("0x") or len(v) != 66:
            raise ValueError("Invalid private key format. Must be 0x followed by 64 hex characters")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("Invalid private key. Must contain only hexadecimal characters")
        return v
    
    @field_validator("default_margin_type")
    @classmethod
    def validate_margin_type(cls, v: str) -> str:
        """Validate margin type"""
        v_upper = v.upper()
        if v_upper not in ("ISOLATED", "CROSSED"):
            raise ValueError("Margin type must be either ISOLATED or CROSSED")
        return v_upper
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        v_upper = v.upper()
        valid_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_levels)}")
        return v_upper
    
    def is_webhook_secret_configured(self) -> bool:
        """Check if webhook secret is configured"""
        return self.webhook_secret is not None and len(self.webhook_secret) > 0
    
    def is_api_key_configured(self) -> bool:
        """Check if API key is configured"""
        return self.api_key is not None and len(self.api_key) > 0
    
    def get_safe_config(self) -> dict:
        """Get configuration dict with sensitive data masked"""
        config = self.model_dump()
        config["asterdex_private_key"] = "***REDACTED***"
        if config.get("webhook_secret"):
            config["webhook_secret"] = "***REDACTED***"
        if config.get("api_key"):
            config["api_key"] = "***REDACTED***"
        return config


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment"""
    global _settings
    _settings = Settings()
    return _settings
