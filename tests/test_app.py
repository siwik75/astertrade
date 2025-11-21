"""Tests for FastAPI application setup and dependency injection."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from src.app import app, get_client, get_trading_service, get_position_service, get_account_service
from src.client.asterdex_client import AsterDEXClient
from src.services.trading_service import TradingService
from src.services.position_service import PositionService
from src.services.account_service import AccountService


def test_app_creation():
    """Test that the FastAPI app is created with correct configuration."""
    assert app.title == "AsterDEX Trading API"
    assert app.version == "1.0.0"
    assert app.docs_url == "/docs"
    assert app.redoc_url == "/redoc"


def test_routes_registered():
    """Test that all expected routes are registered."""
    routes = [route.path for route in app.routes]
    
    # Health endpoints
    assert "/" in routes
    assert "/health" in routes
    
    # Webhook endpoints
    assert "/webhook/tradingview" in routes
    
    # Position endpoints
    assert "/positions" in routes
    assert "/positions/{symbol}" in routes
    assert "/positions/{symbol}/leverage" in routes
    assert "/positions/{symbol}/margin-type" in routes
    
    # Account endpoints
    assert "/account/balance" in routes
    assert "/account/info" in routes
    
    # Order endpoints
    assert "/orders" in routes
    assert "/orders/open" in routes


def test_middleware_configured():
    """Test that middleware is properly configured."""
    # Check CORS middleware is present
    middleware_classes = [m.cls.__name__ for m in app.user_middleware]
    assert "CORSMiddleware" in middleware_classes
    assert "BaseHTTPMiddleware" in middleware_classes  # Request logging middleware


def test_exception_handlers_registered():
    """Test that exception handlers are registered."""
    assert len(app.exception_handlers) > 0


@patch('src.app._client')
def test_get_client_when_initialized(mock_client):
    """Test get_client returns the initialized client."""
    mock_client_instance = Mock(spec=AsterDEXClient)
    
    with patch('src.app._client', mock_client_instance):
        client = get_client()
        assert client == mock_client_instance


def test_get_client_when_not_initialized():
    """Test get_client raises error when client not initialized."""
    with patch('src.app._client', None):
        with pytest.raises(RuntimeError, match="AsterDEX client not initialized"):
            get_client()


@patch('src.app.get_client')
def test_get_trading_service(mock_get_client):
    """Test get_trading_service returns TradingService with client."""
    mock_client = Mock(spec=AsterDEXClient)
    mock_get_client.return_value = mock_client
    
    service = get_trading_service()
    
    assert isinstance(service, TradingService)
    assert service.client == mock_client


@patch('src.app.get_client')
def test_get_position_service(mock_get_client):
    """Test get_position_service returns PositionService with client."""
    mock_client = Mock(spec=AsterDEXClient)
    mock_get_client.return_value = mock_client
    
    service = get_position_service()
    
    assert isinstance(service, PositionService)
    assert service.client == mock_client


@patch('src.app.get_client')
def test_get_account_service(mock_get_client):
    """Test get_account_service returns AccountService with client."""
    mock_client = Mock(spec=AsterDEXClient)
    mock_get_client.return_value = mock_client
    
    service = get_account_service()
    
    assert isinstance(service, AccountService)
    assert service.client == mock_client


@pytest.mark.skip(reason="Requires environment configuration for lifespan")
def test_health_endpoint():
    """Test health endpoint is accessible."""
    with TestClient(app) as client:
        response = client.get("/health")
        # May fail due to missing config, but endpoint should exist
        assert response.status_code in [200, 503]


@pytest.mark.skip(reason="Requires environment configuration for lifespan")
def test_root_endpoint_redirects():
    """Test root endpoint redirects to docs."""
    with TestClient(app) as client:
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/docs"
