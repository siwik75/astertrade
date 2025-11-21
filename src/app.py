"""Main FastAPI application with dependency injection and middleware setup."""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .logging_config import configure_logging, get_logger
from .client.authenticator import AsterDEXAuthenticator
from .client.asterdex_client import AsterDEXClient, AsterDEXClientError
from .services.trading_service import TradingService
from .services.position_service import PositionService
from .services.account_service import AccountService
from .error_handlers import register_exception_handlers

# Import routers
from .api import (
    health_router,
    webhook_router,
    positions_router,
    account_router,
    orders_router
)


# Initialize with default logging
configure_logging()
logger = get_logger(__name__)


# Global client instance
_client: AsterDEXClient = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    settings = get_settings()
    
    # Reconfigure logging with settings
    configure_logging(settings.log_level)
    
    logger.info("application_starting")
    
    # Log safe configuration
    logger.info(
        "configuration_loaded",
        base_url=settings.asterdex_base_url,
        webhook_secret_configured=settings.is_webhook_secret_configured(),
        default_leverage=settings.default_leverage,
        default_margin_type=settings.default_margin_type
    )
    
    # Initialize AsterDEX client
    global _client
    authenticator = AsterDEXAuthenticator(
        user=settings.asterdex_user_address,
        signer=settings.asterdex_signer_address,
        private_key=settings.asterdex_private_key
    )
    
    _client = AsterDEXClient(
        base_url=settings.asterdex_base_url,
        authenticator=authenticator,
        timeout=settings.request_timeout,
        max_retries=settings.max_retries,
        rate_limit_retry_delay=settings.rate_limit_retry_delay
    )
    
    logger.info("asterdex_client_initialized")
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")
    
    # Close HTTP client connections
    if _client:
        await _client.close()
        logger.info("asterdex_client_closed")
    
    logger.info("application_shutdown_complete")


# Create FastAPI application
app = FastAPI(
    title="AsterDEX Trading API",
    description="""
    FastAPI server for automated trading on AsterDEX perpetual futures platform.
    
    This API receives webhook signals from TradingView and executes trading operations
    including opening, increasing, decreasing, and closing positions.
    
    ## Features
    
    - **Webhook Integration**: Receive TradingView alerts and execute trades automatically
    - **Position Management**: Query and manage open positions with leverage and margin controls
    - **Account Information**: Access balance and account details
    - **Order History**: View historical and open orders
    - **Secure Authentication**: Web3 ECDSA signature-based authentication with AsterDEX
    
    ## Authentication
    
    All requests to AsterDEX are authenticated using Web3 ECDSA signatures.
    Webhook endpoints support optional secret token validation via `X-Webhook-Secret` header.
    
    ## Getting Started
    
    1. Configure your environment variables (see `.env.example`)
    2. Start the server: `uvicorn main:app --reload`
    3. Visit `/docs` for interactive API documentation
    4. Configure TradingView webhooks to point to `/webhook/tradingview`
    
    ## Documentation
    
    - **Interactive Docs**: `/docs` (Swagger UI)
    - **Alternative Docs**: `/redoc` (ReDoc)
    - **OpenAPI Schema**: `/openapi.json`
    
    For detailed API documentation, see [API_DOCUMENTATION.md](https://github.com/your-repo/API_DOCUMENTATION.md)
    """,
    version="1.0.0",
    contact={
        "name": "AsterDEX Trading API",
        "url": "https://github.com/your-repo",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {
            "name": "Health",
            "description": "Health check and status endpoints for monitoring server availability."
        },
        {
            "name": "Webhook",
            "description": "TradingView webhook endpoints for receiving trading signals and executing automated trades."
        },
        {
            "name": "Positions",
            "description": "Position management endpoints for querying open positions and configuring leverage/margin settings."
        },
        {
            "name": "Account",
            "description": "Account information endpoints for querying balance and account details."
        },
        {
            "name": "Orders",
            "description": "Order management endpoints for querying order history and open orders."
        }
    ]
)


# Register exception handlers
register_exception_handlers(app)


# Configure CORS middleware
# Note: Configure allow_origins appropriately for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming HTTP requests and responses.
    
    Captures request details, response status, and processing time.
    """
    start_time = time.time()
    
    # Log request
    logger.info(
        "request_received",
        method=request.method,
        path=request.url.path,
        client_host=request.client.host if request.client else None,
    )
    
    # Process request
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time_ms=round(process_time * 1000, 2)
        )
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    except Exception as e:
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log error
        logger.error(
            "request_failed",
            method=request.method,
            path=request.url.path,
            error=str(e),
            process_time_ms=round(process_time * 1000, 2),
            exc_info=True
        )
        
        # Re-raise to let FastAPI handle it
        raise





# Dependency injection functions
def get_client() -> AsterDEXClient:
    """
    Get AsterDEX client instance.
    
    Returns:
        Initialized AsterDEX client
        
    Raises:
        RuntimeError: If client is not initialized
    """
    if _client is None:
        raise RuntimeError("AsterDEX client not initialized")
    return _client


def get_trading_service() -> TradingService:
    """
    Get trading service instance.
    
    Returns:
        Trading service with injected client
    """
    client = get_client()
    return TradingService(client)


def get_position_service() -> PositionService:
    """
    Get position service instance.
    
    Returns:
        Position service with injected client
    """
    client = get_client()
    return PositionService(client)


def get_account_service() -> AccountService:
    """
    Get account service instance.
    
    Returns:
        Account service with injected client
    """
    client = get_client()
    return AccountService(client)


# Register routers
app.include_router(health_router)
app.include_router(webhook_router)
app.include_router(positions_router)
app.include_router(account_router)
app.include_router(orders_router)


# Override dependencies using FastAPI's dependency_overrides
# This must be done AFTER including routers
from .api import webhook as webhook_module
from .api import positions as positions_module
from .api import account as account_module
from .api import orders as orders_module

app.dependency_overrides[webhook_module.get_trading_service] = get_trading_service
app.dependency_overrides[positions_module.get_position_service] = get_position_service
app.dependency_overrides[account_module.get_account_service] = get_account_service
app.dependency_overrides[orders_module.get_trading_service] = get_trading_service


logger.info("application_configured")
