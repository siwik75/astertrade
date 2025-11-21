"""Pytest configuration and fixtures for tests."""

import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock
from dotenv import load_dotenv

# Load test environment variables BEFORE importing app
test_env_path = Path(__file__).parent.parent / ".env.test"
if test_env_path.exists():
    load_dotenv(test_env_path)

from src.app import app
from src.api.webhook import get_trading_service


# Global mock service that can be configured by tests
_mock_service = Mock()
_mock_service.open_position = AsyncMock(return_value={})
_mock_service.close_position = AsyncMock(return_value={})
_mock_service.increase_position = AsyncMock(return_value={})
_mock_service.decrease_position = AsyncMock(return_value={})


def get_mock_trading_service():
    """Return the global mock trading service."""
    return _mock_service


# Set up dependency override at module level (before any tests run)
app.dependency_overrides[get_trading_service] = get_mock_trading_service


@pytest.fixture(scope="module")
def client():
    """Create a test client for the module."""
    # The dependency override is already set at module level
    # Create a single TestClient instance for all tests in the module
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def mock_trading_service():
    """Provide a fresh mock trading service for individual tests."""
    return get_mock_trading_service()
