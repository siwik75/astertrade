"""Order management endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status

from ..models.responses import OrderResponse
from ..services.trading_service import TradingService
from ..client.asterdex_client import AsterDEXClientError
from ..logging_config import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/orders", tags=["Orders"])


def get_trading_service() -> TradingService:
    """Dependency to get trading service instance."""
    # This will be properly implemented in the main app setup
    raise NotImplementedError("Trading service dependency not configured")


@router.get(
    "",
    response_model=List[OrderResponse],
    summary="Get Order History",
    description="Retrieve historical orders with filtering by symbol and optional time range.",
    responses={
        200: {
            "description": "List of orders",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "order_id": 12345678,
                            "symbol": "BTCUSDT",
                            "side": "BUY",
                            "type": "MARKET",
                            "status": "FILLED",
                            "quantity": "0.001",
                            "price": None,
                            "executed_qty": "0.001",
                            "avg_price": "43250.50"
                        }
                    ]
                }
            }
        },
        400: {
            "description": "Missing required parameter",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Bad Request",
                        "detail": "Symbol parameter is required",
                        "code": 400
                    }
                }
            }
        }
    }
)
async def get_orders(
    symbol: Optional[str] = Query(None, description="Trading pair symbol (e.g., BTCUSDT)"),
    start_time: Optional[int] = Query(None, description="Start time in milliseconds", ge=0),
    end_time: Optional[int] = Query(None, description="End time in milliseconds", ge=0),
    limit: int = Query(50, description="Number of orders to return", ge=1, le=1000),
    trading_service: TradingService = Depends(get_trading_service)
) -> List[OrderResponse]:
    """
    Get order history.
    
    Returns historical orders with optional filtering by symbol and time range.
    Results are paginated with a default limit of 50 orders.
    
    Args:
        symbol: Optional trading pair symbol to filter by
        start_time: Optional start time in milliseconds
        end_time: Optional end time in milliseconds
        limit: Maximum number of orders to return (1-1000, default 50)
        trading_service: Trading service dependency
        
    Returns:
        List of order responses
        
    Raises:
        HTTPException: If validation fails or API request fails
    """
    logger.info(
        "fetching_orders",
        symbol=symbol,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    # Validate that symbol is provided (required by AsterDEX API)
    if not symbol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Symbol parameter is required"
        )
    
    try:
        orders = await trading_service.client.get_all_orders(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        logger.info(
            "orders_fetched",
            symbol=symbol,
            count=len(orders)
        )
        
        return [OrderResponse(**order) for order in orders]
    
    except AsterDEXClientError as e:
        logger.error(
            "failed_to_fetch_orders",
            symbol=symbol,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AsterDEX API error: {str(e)}"
        )
    
    except Exception as e:
        logger.error(
            "unexpected_error_fetching_orders",
            symbol=symbol,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/open",
    response_model=List[OrderResponse],
    summary="Get Open Orders",
    description="Retrieve all currently open (unfilled) orders, optionally filtered by symbol.",
    responses={
        200: {
            "description": "List of open orders",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "order_id": 12345680,
                            "symbol": "BTCUSDT",
                            "side": "BUY",
                            "type": "LIMIT",
                            "status": "NEW",
                            "quantity": "0.001",
                            "price": "42000.00",
                            "executed_qty": "0.000",
                            "avg_price": None
                        }
                    ]
                }
            }
        }
    }
)
async def get_open_orders(
    symbol: Optional[str] = Query(None, description="Trading pair symbol (e.g., BTCUSDT)"),
    trading_service: TradingService = Depends(get_trading_service)
) -> List[OrderResponse]:
    """
    Get open orders.
    
    Returns all currently open (unfilled) orders, optionally filtered by symbol.
    If no symbol is provided, returns open orders for all trading pairs.
    
    Args:
        symbol: Optional trading pair symbol to filter by
        trading_service: Trading service dependency
        
    Returns:
        List of open order responses
        
    Raises:
        HTTPException: If API request fails
    """
    logger.info(
        "fetching_open_orders",
        symbol=symbol
    )
    
    try:
        orders = await trading_service.client.get_open_orders(symbol=symbol)
        
        logger.info(
            "open_orders_fetched",
            symbol=symbol,
            count=len(orders)
        )
        
        return [OrderResponse(**order) for order in orders]
    
    except AsterDEXClientError as e:
        logger.error(
            "failed_to_fetch_open_orders",
            symbol=symbol,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AsterDEX API error: {str(e)}"
        )
    
    except Exception as e:
        logger.error(
            "unexpected_error_fetching_open_orders",
            symbol=symbol,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
