"""Position management endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, status

from ..models.requests import LeverageUpdateRequest, MarginTypeUpdateRequest
from ..models.responses import PositionResponse
from ..services.position_service import PositionService
from ..client.asterdex_client import AsterDEXClientError
from ..logging_config import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/positions", tags=["Positions"])


def get_position_service() -> PositionService:
    """Dependency to get position service instance."""
    # This will be properly implemented in the main app setup
    raise NotImplementedError("Position service dependency not configured")


@router.get(
    "",
    response_model=List[PositionResponse],
    summary="Get All Open Positions",
    description="Retrieve all current open positions with non-zero amounts.",
    responses={
        200: {
            "description": "List of open positions",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "symbol": "BTCUSDT",
                            "position_side": "BOTH",
                            "position_amt": "0.001",
                            "entry_price": "43250.50",
                            "mark_price": "43255.00",
                            "unrealized_profit": "0.0045",
                            "leverage": 10,
                            "margin_type": "CROSSED",
                            "liquidation_price": "39000.00"
                        }
                    ]
                }
            }
        }
    }
)
async def get_all_positions(
    position_service: PositionService = Depends(get_position_service)
) -> List[PositionResponse]:
    """
    Get all open positions.
    
    Returns a list of all current positions with non-zero amounts.
    Positions with zero amount are filtered out.
    
    Args:
        position_service: Position service dependency
        
    Returns:
        List of position responses
        
    Raises:
        HTTPException: If API request fails
    """
    logger.info("fetching_all_positions")
    
    try:
        positions = await position_service.get_positions()
        
        logger.info(
            "positions_fetched",
            count=len(positions)
        )
        
        return [PositionResponse(**pos) for pos in positions]
    
    except AsterDEXClientError as e:
        logger.error(
            "failed_to_fetch_positions",
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AsterDEX API error: {str(e)}"
        )
    
    except Exception as e:
        logger.error(
            "unexpected_error_fetching_positions",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/{symbol}",
    response_model=PositionResponse,
    summary="Get Position by Symbol",
    description="Retrieve position information for a specific trading pair.",
    responses={
        200: {
            "description": "Position information",
            "content": {
                "application/json": {
                    "example": {
                        "symbol": "BTCUSDT",
                        "position_side": "BOTH",
                        "position_amt": "0.001",
                        "entry_price": "43250.50",
                        "mark_price": "43255.00",
                        "unrealized_profit": "0.0045",
                        "leverage": 10,
                        "margin_type": "CROSSED",
                        "liquidation_price": "39000.00"
                    }
                }
            }
        },
        404: {
            "description": "Position not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Position not found",
                        "detail": "No open position found for symbol BTCUSDT",
                        "code": 404
                    }
                }
            }
        }
    }
)
async def get_position(
    symbol: str,
    position_service: PositionService = Depends(get_position_service)
) -> PositionResponse:
    """
    Get position for a specific symbol.
    
    Returns the current position information for the specified trading pair.
    Returns 404 if no open position exists for the symbol.
    
    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT)
        position_service: Position service dependency
        
    Returns:
        Position response for the symbol
        
    Raises:
        HTTPException: If position not found or API request fails
    """
    logger.info("fetching_position", symbol=symbol)
    
    try:
        position = await position_service.get_position_by_symbol(symbol)
        
        if position is None:
            logger.warning("position_not_found", symbol=symbol)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No open position found for symbol {symbol}"
            )
        
        logger.info("position_fetched", symbol=symbol)
        
        return PositionResponse(**position)
    
    except HTTPException:
        raise
    
    except AsterDEXClientError as e:
        logger.error(
            "failed_to_fetch_position",
            symbol=symbol,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AsterDEX API error: {str(e)}"
        )
    
    except Exception as e:
        logger.error(
            "unexpected_error_fetching_position",
            symbol=symbol,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post(
    "/{symbol}/leverage",
    summary="Update Position Leverage",
    description="Change the leverage setting for a specific trading pair (1-125x).",
    responses={
        200: {
            "description": "Leverage updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Leverage updated to 20x for BTCUSDT",
                        "symbol": "BTCUSDT",
                        "leverage": 20
                    }
                }
            }
        },
        400: {
            "description": "Invalid leverage value",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Invalid leverage",
                        "detail": "Leverage must be between 1 and 125",
                        "code": 400
                    }
                }
            }
        }
    }
)
async def update_leverage(
    symbol: str,
    request: LeverageUpdateRequest,
    position_service: PositionService = Depends(get_position_service)
) -> dict:
    """
    Update leverage for a symbol.
    
    Changes the leverage setting for the specified trading pair.
    Leverage must be between 1 and 125.
    
    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT)
        request: Leverage update request
        position_service: Position service dependency
        
    Returns:
        Confirmation of leverage update
        
    Raises:
        HTTPException: If validation fails or API request fails
    """
    logger.info(
        "updating_leverage",
        symbol=symbol,
        leverage=request.leverage
    )
    
    try:
        result = await position_service.update_leverage(
            symbol=symbol,
            leverage=request.leverage
        )
        
        logger.info(
            "leverage_updated",
            symbol=symbol,
            leverage=request.leverage
        )
        
        return {
            "success": True,
            "message": f"Leverage updated to {request.leverage}x for {symbol}",
            "symbol": symbol,
            "leverage": request.leverage,
            "result": result
        }
    
    except ValueError as e:
        logger.error(
            "invalid_leverage_value",
            symbol=symbol,
            leverage=request.leverage,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except AsterDEXClientError as e:
        logger.error(
            "failed_to_update_leverage",
            symbol=symbol,
            leverage=request.leverage,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AsterDEX API error: {str(e)}"
        )
    
    except Exception as e:
        logger.error(
            "unexpected_error_updating_leverage",
            symbol=symbol,
            leverage=request.leverage,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post(
    "/{symbol}/margin-type",
    summary="Update Margin Type",
    description="Change the margin type for a specific trading pair (ISOLATED or CROSSED).",
    responses={
        200: {
            "description": "Margin type updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Margin type updated to ISOLATED for BTCUSDT",
                        "symbol": "BTCUSDT",
                        "margin_type": "ISOLATED"
                    }
                }
            }
        },
        400: {
            "description": "Invalid margin type",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Invalid margin type",
                        "detail": "Margin type must be ISOLATED or CROSSED",
                        "code": 400
                    }
                }
            }
        }
    }
)
async def update_margin_type(
    symbol: str,
    request: MarginTypeUpdateRequest,
    position_service: PositionService = Depends(get_position_service)
) -> dict:
    """
    Update margin type for a symbol.
    
    Changes the margin type setting for the specified trading pair.
    Margin type must be either ISOLATED or CROSSED.
    
    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT)
        request: Margin type update request
        position_service: Position service dependency
        
    Returns:
        Confirmation of margin type update
        
    Raises:
        HTTPException: If validation fails or API request fails
    """
    logger.info(
        "updating_margin_type",
        symbol=symbol,
        margin_type=request.margin_type
    )
    
    try:
        result = await position_service.update_margin_type(
            symbol=symbol,
            margin_type=request.margin_type
        )
        
        logger.info(
            "margin_type_updated",
            symbol=symbol,
            margin_type=request.margin_type
        )
        
        return {
            "success": True,
            "message": f"Margin type updated to {request.margin_type} for {symbol}",
            "symbol": symbol,
            "margin_type": request.margin_type,
            "result": result
        }
    
    except ValueError as e:
        logger.error(
            "invalid_margin_type_value",
            symbol=symbol,
            margin_type=request.margin_type,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except AsterDEXClientError as e:
        logger.error(
            "failed_to_update_margin_type",
            symbol=symbol,
            margin_type=request.margin_type,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AsterDEX API error: {str(e)}"
        )
    
    except Exception as e:
        logger.error(
            "unexpected_error_updating_margin_type",
            symbol=symbol,
            margin_type=request.margin_type,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
