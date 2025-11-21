"""Tests for error handling and validation."""

import pytest
from unittest.mock import Mock, AsyncMock
import httpx

from src.app import app
from src.api.webhook import get_trading_service
from src.exceptions import (
    ValidationError,
    AuthenticationError,
    ResourceNotFoundError,
    RateLimitExceededError,
    ExternalAPIError,
    TimeoutError,
)
from src.client.asterdex_client import (
    AsterDEXClientError,
    RateLimitError,
    ServerError
)
from src.services.trading_service import (
    PositionNotFoundError,
    InvalidParameterError
)


class TestCustomExceptions:
    """Test custom exception classes."""
    
    def test_validation_error(self):
        """Test ValidationError exception."""
        exc = ValidationError(
            message="Invalid parameter",
            details={"field": "quantity"}
        )
        assert exc.status_code == 400
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.message == "Invalid parameter"
        assert exc.details["field"] == "quantity"
    
    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        exc = AuthenticationError()
        assert exc.status_code == 401
        assert exc.error_code == "AUTHENTICATION_ERROR"
    
    def test_resource_not_found_error(self):
        """Test ResourceNotFoundError exception."""
        exc = ResourceNotFoundError(message="Position not found")
        assert exc.status_code == 404
        assert exc.error_code == "RESOURCE_NOT_FOUND"
    
    def test_rate_limit_exceeded_error(self):
        """Test RateLimitExceededError exception."""
        exc = RateLimitExceededError(retry_after=60)
        assert exc.status_code == 429
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.retry_after == 60
    
    def test_external_api_error(self):
        """Test ExternalAPIError exception."""
        exc = ExternalAPIError(
            message="API error",
            original_error_code=-2019,
            original_error_message="Insufficient margin"
        )
        assert exc.status_code == 502
        assert exc.error_code == "EXTERNAL_API_ERROR"
        assert exc.original_error_code == -2019
        assert exc.details["original_error_code"] == -2019
    
    def test_timeout_error(self):
        """Test TimeoutError exception."""
        exc = TimeoutError(timeout_seconds=30)
        assert exc.status_code == 504
        assert exc.error_code == "TIMEOUT_ERROR"
        assert exc.timeout_seconds == 30


class TestExceptionHandlers:
    """Test exception handlers."""
    
    def test_position_not_found_handler(self, client):
        """Test PositionNotFoundError is handled correctly."""
        # Import the global mock from conftest
        from tests.conftest import _mock_service
        
        # Configure the global mock to raise PositionNotFoundError
        _mock_service.close_position = AsyncMock(
            side_effect=PositionNotFoundError("No position found for BTCUSDT")
        )
        
        # Make request
        response = client.post(
            "/webhook/tradingview",
            json={
                "action": "close",
                "symbol": "BTCUSDT"
            }
        )
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "detail" in data
        assert "BTCUSDT" in data["detail"]
        
        # Reset mock for next test
        _mock_service.close_position = AsyncMock(return_value={})
    
    def test_invalid_parameter_handler(self, client):
        """Test InvalidParameterError is handled correctly."""
        # Mock service to raise InvalidParameterError
        mock_service = Mock()
        mock_service.open_position = AsyncMock(
            side_effect=InvalidParameterError("Quantity must be positive")
        )
        
        # Override dependency for this test
        app.dependency_overrides[get_trading_service] = lambda: mock_service
        
        # Make request
        response = client.post(
            "/webhook/tradingview",
            json={
                "action": "open",
                "symbol": "BTCUSDT",
                "side": "BUY",
                "quantity": "0.001"
            }
        )
        
        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "detail" in data
    
    def test_asterdex_client_error_handler(self, client):
        """Test AsterDEXClientError is handled correctly."""
        # Mock service to raise AsterDEXClientError
        mock_service = Mock()
        mock_service.open_position = AsyncMock(
            side_effect=AsterDEXClientError("API connection failed")
        )
        
        # Override dependency for this test
        app.dependency_overrides[get_trading_service] = lambda: mock_service
        
        # Make request
        response = client.post(
            "/webhook/tradingview",
            json={
                "action": "open",
                "symbol": "BTCUSDT",
                "side": "BUY",
                "quantity": "0.001"
            }
        )
        
        # Verify response
        assert response.status_code == 502
        data = response.json()
        assert "error" in data
        assert "detail" in data
    
    def test_validation_error_handler(self, client):
        """Test request validation error is handled correctly."""
        # Make request with missing required fields
        response = client.post(
            "/webhook/tradingview",
            json={
                "action": "open",
                "symbol": "BTCUSDT"
                # Missing 'side' and 'quantity'
            }
        )
        
        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"] == "ValidationError"
        assert "validation_errors" in data


class TestErrorResponseFormat:
    """Test error response format."""
    
    def test_error_response_structure(self, client):
        """Test error response has correct structure."""
        # Make request that will fail validation
        response = client.post(
            "/webhook/tradingview",
            json={}  # Empty payload
        )
        
        # Verify response structure
        assert response.status_code == 400
        data = response.json()
        
        # Check required fields
        assert "error" in data
        assert "detail" in data
        assert "code" in data
        assert "timestamp" in data
        
        # Verify timestamp is a number
        assert isinstance(data["timestamp"], int)
        assert data["timestamp"] > 0
    
    def test_error_response_with_original_error(self, client):
        """Test error response includes original AsterDEX error details."""
        # Mock service to raise error with AsterDEX details
        mock_service = Mock()
        mock_service.open_position = AsyncMock(
            side_effect=AsterDEXClientError(
                "AsterDEX error -2019: Margin is insufficient"
            )
        )
        
        # Override dependency for this test
        app.dependency_overrides[get_trading_service] = lambda: mock_service
        
        # Make request
        response = client.post(
            "/webhook/tradingview",
            json={
                "action": "open",
                "symbol": "BTCUSDT",
                "side": "BUY",
                "quantity": "0.001"
            }
        )
        
        # Verify response includes error details
        assert response.status_code == 502
        data = response.json()
        assert "error" in data
        assert "detail" in data
        assert "AsterDEX" in data["detail"]


class TestTimeoutHandling:
    """Test timeout handling."""
    
    def test_timeout_error_response(self, client):
        """Test timeout errors return 504 status."""
        # Mock service to raise timeout
        mock_service = Mock()
        mock_service.open_position = AsyncMock(
            side_effect=httpx.TimeoutException("Request timeout")
        )
        
        # Override dependency for this test
        app.dependency_overrides[get_trading_service] = lambda: mock_service
        
        # Make request
        response = client.post(
            "/webhook/tradingview",
            json={
                "action": "open",
                "symbol": "BTCUSDT",
                "side": "BUY",
                "quantity": "0.001"
            }
        )
        
        # Verify response
        assert response.status_code == 504
        data = response.json()
        assert "error" in data
        assert "timeout" in data["detail"].lower()


class TestRateLimitHandling:
    """Test rate limit handling."""
    
    def test_rate_limit_error_response(self, client):
        """Test rate limit errors return 429 status."""
        # Mock service to raise rate limit error
        mock_service = Mock()
        mock_service.open_position = AsyncMock(
            side_effect=RateLimitError("Rate limit exceeded")
        )
        
        # Override dependency for this test
        app.dependency_overrides[get_trading_service] = lambda: mock_service
        
        # Make request
        response = client.post(
            "/webhook/tradingview",
            json={
                "action": "open",
                "symbol": "BTCUSDT",
                "side": "BUY",
                "quantity": "0.001"
            }
        )
        
        # Verify response
        assert response.status_code == 429
        data = response.json()
        assert "error" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
