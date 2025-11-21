"""Webhook endpoint for TradingView signals."""

import time
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Depends, status

from ..models.requests import WebhookRequest, StrategyWebhookRequest
from ..models.responses import WebhookResponse, OrderResponse, PositionResponse
from ..services.trading_service import (
    TradingService,
    PositionNotFoundError,
    InvalidParameterError
)
from ..client.asterdex_client import AsterDEXClientError
from ..config import get_settings
from ..logging_config import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/webhook", tags=["Webhook"])


def get_trading_service() -> TradingService:
    """Dependency to get trading service instance."""
    # This will be properly implemented in the main app setup
    # For now, this is a placeholder that will be overridden
    raise NotImplementedError("Trading service dependency not configured")


@router.post(
    "/tradingview",
    response_model=WebhookResponse,
    summary="Execute TradingView Webhook Signal",
    description="""
    Receive TradingView webhook signals and execute automated trading operations on AsterDEX.
    
    This endpoint processes webhook alerts from TradingView and translates them into
    trading actions on the AsterDEX perpetual futures platform.
    """,
    responses={
        200: {
            "description": "Trading action executed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Position opened successfully for BTCUSDT",
                        "order": {
                            "order_id": 12345678,
                            "symbol": "BTCUSDT",
                            "side": "BUY",
                            "type": "MARKET",
                            "status": "FILLED",
                            "quantity": "0.001",
                            "price": None,
                            "executed_qty": "0.001",
                            "avg_price": "43250.50"
                        },
                        "position": {
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
            }
        },
        400: {
            "description": "Invalid request parameters",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Invalid parameter",
                        "detail": "Quantity is required for open action",
                        "code": 400
                    }
                }
            }
        },
        401: {
            "description": "Invalid or missing webhook secret",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Unauthorized",
                        "detail": "Invalid webhook secret",
                        "code": 401
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
                        "detail": "No open position for symbol BTCUSDT",
                        "code": 404
                    }
                }
            }
        }
    }
)
async def tradingview_webhook(
    request: WebhookRequest,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    trading_service: TradingService = Depends(get_trading_service)
) -> WebhookResponse:
    """
    Receive TradingView webhook and execute trading action.
    
    This endpoint accepts webhook signals from TradingView and executes
    the corresponding trading operation on AsterDEX.
    
    **Supported Actions:**
    - `open`: Open a new position (requires side, quantity)
    - `increase`: Add to existing position (requires quantity)
    - `decrease`: Reduce position size (requires quantity)
    - `close`: Close entire position
    
    **Authentication:**
    If webhook secret is configured, requests must include the
    `X-Webhook-Secret` header with the correct value.
    
    Args:
        request: Webhook request payload
        x_webhook_secret: Optional webhook secret header
        trading_service: Trading service dependency
        
    Returns:
        WebhookResponse with operation result
        
    Raises:
        HTTPException: For validation errors, authentication failures, or API errors
    """
    settings = get_settings()
    
    # Log incoming webhook request
    logger.info(
        "webhook_received",
        action=request.action,
        symbol=request.symbol,
        timestamp=int(time.time() * 1000)
    )
    
    # Validate webhook secret if configured
    # Check both header and body (body takes precedence for TradingView compatibility)
    if settings.is_webhook_secret_configured():
        provided_secret = request.webhook_secret or x_webhook_secret
        
        if not provided_secret:
            logger.warning(
                "webhook_missing_secret",
                symbol=request.symbol
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Webhook secret required but not provided"
            )
        
        if provided_secret != settings.webhook_secret:
            logger.warning(
                "webhook_invalid_secret",
                symbol=request.symbol
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook secret"
            )
    
    try:
        # Route to appropriate trading service method based on action
        if request.action == "open":
            # Validate required fields for open action
            if not request.side:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Side (BUY/SELL) is required for open action"
                )
            if not request.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quantity is required for open action"
                )
            
            # Open new position
            result = await trading_service.open_position(
                symbol=request.symbol,
                side=request.side,
                quantity=request.quantity,
                order_type=request.order_type,
                price=request.price
            )
            
            # Get position info
            position_data = None
            try:
                from ..services.position_service import PositionService
                position_service = PositionService(trading_service.client)
                position_data = await position_service.get_position_by_symbol(request.symbol)
            except Exception as e:
                logger.warning("failed_to_fetch_position", error=str(e))
            
            return WebhookResponse(
                success=True,
                message=f"Position opened successfully for {request.symbol}",
                order=OrderResponse(**result) if result else None,
                position=PositionResponse(**position_data) if position_data else None
            )
        
        elif request.action == "increase":
            # Validate required fields for increase action
            if not request.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quantity is required for increase action"
                )
            
            # Increase existing position
            result = await trading_service.increase_position(
                symbol=request.symbol,
                quantity=request.quantity,
                order_type=request.order_type,
                price=request.price
            )
            
            return WebhookResponse(
                success=True,
                message=f"Position increased successfully for {request.symbol}",
                order=OrderResponse(**result["order"]) if result.get("order") else None,
                position=PositionResponse(**result["position"]) if result.get("position") else None
            )
        
        elif request.action == "decrease":
            # Validate required fields for decrease action
            if not request.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quantity is required for decrease action"
                )
            
            # Decrease existing position
            result = await trading_service.decrease_position(
                symbol=request.symbol,
                quantity=request.quantity,
                order_type=request.order_type,
                price=request.price
            )
            
            return WebhookResponse(
                success=True,
                message=f"Position decreased successfully for {request.symbol}",
                order=OrderResponse(**result["order"]) if result.get("order") else None,
                position=PositionResponse(**result["position"]) if result.get("position") else None
            )
        
        elif request.action == "close":
            # Close entire position
            result = await trading_service.close_position(symbol=request.symbol)
            
            return WebhookResponse(
                success=True,
                message=f"Position closed successfully for {request.symbol}",
                order=OrderResponse(**result["order"]) if result.get("order") else None,
                position=PositionResponse(**result["position"]) if result.get("position") else None
            )
        
        else:
            # This should not happen due to pydantic validation
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported action: {request.action}"
            )
    
    except PositionNotFoundError as e:
        logger.error(
            "webhook_position_not_found",
            symbol=request.symbol,
            action=request.action,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except InvalidParameterError as e:
        logger.error(
            "webhook_invalid_parameter",
            symbol=request.symbol,
            action=request.action,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except AsterDEXClientError as e:
        logger.error(
            "webhook_asterdex_error",
            symbol=request.symbol,
            action=request.action,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AsterDEX API error: {str(e)}"
        )
    
    except Exception as e:
        logger.error(
            "webhook_unexpected_error",
            symbol=request.symbol,
            action=request.action,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post(
    "/tradingview-strategy",
    response_model=WebhookResponse,
    summary="Execute TradingView Strategy Webhook",
    description="""
    Receive TradingView strategy webhook signals and automatically determine the correct action.
    
    This endpoint is designed for TradingView strategy alerts that use {{strategy.order.action}},
    {{strategy.order.contracts}}, and {{strategy.position_size}} variables. It automatically
    determines whether to open, close, increase, or decrease positions based on the order flow.
    """,
    responses={
        200: {
            "description": "Strategy order executed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Position opened successfully for BTCUSDT",
                        "order": {
                            "order_id": 12345678,
                            "symbol": "BTCUSDT",
                            "side": "BUY",
                            "type": "MARKET",
                            "status": "FILLED",
                            "quantity": "0.575181",
                            "executed_qty": "0.575181",
                            "avg_price": "43250.50"
                        }
                    }
                }
            }
        }
    }
)
async def tradingview_strategy_webhook(
    request: StrategyWebhookRequest,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    trading_service: TradingService = Depends(get_trading_service)
) -> WebhookResponse:
    """
    Receive TradingView strategy webhook and automatically execute the correct action.
    
    This endpoint intelligently determines the action based on:
    - Current position on AsterDEX
    - Strategy order action (buy/sell)
    - Order contracts
    - Target position size
    
    **Logic:**
    - If current position is 0 and order creates position → Open
    - If order brings position to 0 → Close
    - If order increases position in same direction → Increase
    - If order reduces position (opposite direction) → Decrease
    - If order flips position (goes through 0) → Close + Open
    
    Args:
        request: Strategy webhook request payload
        x_webhook_secret: Optional webhook secret header
        trading_service: Trading service dependency
        
    Returns:
        WebhookResponse with operation result
    """
    settings = get_settings()
    
    # Log incoming webhook request
    logger.info(
        "strategy_webhook_received",
        order_action=request.order_action,
        symbol=request.symbol,
        contracts=str(request.contracts),
        position_size=str(request.position_size),
        timestamp=int(time.time() * 1000)
    )
    
    # Validate webhook secret if configured
    # Check both header and body (body takes precedence for TradingView compatibility)
    if settings.is_webhook_secret_configured():
        provided_secret = request.webhook_secret or x_webhook_secret
        
        if not provided_secret:
            logger.warning("strategy_webhook_missing_secret", symbol=request.symbol)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Webhook secret required but not provided"
            )
        
        if provided_secret != settings.webhook_secret:
            logger.warning("strategy_webhook_invalid_secret", symbol=request.symbol)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook secret"
            )
    
    try:
        # Get current position from AsterDEX
        from ..services.position_service import PositionService
        position_service = PositionService(trading_service.client)
        current_position = await position_service.get_position_by_symbol(request.symbol)
        
        # Determine current position size (0 if no position)
        current_size = Decimal("0")
        if current_position and "positionAmt" in current_position:
            current_size = Decimal(str(current_position["positionAmt"]))
        
        logger.info(
            "strategy_position_analysis",
            symbol=request.symbol,
            current_size=str(current_size),
            target_size=str(request.position_size),
            order_action=request.order_action,
            contracts=str(request.contracts)
        )
        
        # Determine the action based on position changes
        action = None
        side = None
        quantity = request.contracts
        
        # Case 1: Opening a new position (current is 0, target is not 0)
        if current_size == 0 and request.position_size != 0:
            action = "open"
            side = "BUY" if request.position_size > 0 else "SELL"
            quantity = abs(request.position_size)
            
        # Case 2: Closing position (target is 0)
        elif request.position_size == 0 and current_size != 0:
            action = "close"
            
        # Case 3: Position flip (goes through zero) - close then open
        elif (current_size > 0 and request.position_size < 0) or \
             (current_size < 0 and request.position_size > 0):
            # First close the current position
            logger.info(
                "strategy_position_flip_detected",
                symbol=request.symbol,
                current_size=str(current_size),
                target_size=str(request.position_size)
            )
            
            close_result = await trading_service.close_position(symbol=request.symbol)
            
            # Then open new position in opposite direction
            side = "BUY" if request.position_size > 0 else "SELL"
            open_result = await trading_service.open_position(
                symbol=request.symbol,
                side=side,
                quantity=abs(request.position_size),
                order_type=request.order_type,
                price=request.price
            )
            
            return WebhookResponse(
                success=True,
                message=f"Position flipped successfully for {request.symbol}",
                order=OrderResponse(**open_result) if open_result else None,
                position=None
            )
        
        # Case 4: Increasing position (same direction, larger size)
        elif (current_size > 0 and request.position_size > current_size) or \
             (current_size < 0 and request.position_size < current_size):
            action = "increase"
            quantity = abs(request.position_size - current_size)
            
        # Case 5: Decreasing position (opposite direction, smaller size)
        elif (current_size > 0 and request.position_size < current_size and request.position_size >= 0) or \
             (current_size < 0 and request.position_size > current_size and request.position_size <= 0):
            action = "decrease"
            quantity = abs(current_size - request.position_size)
        
        else:
            # Unexpected case - log and return error
            logger.error(
                "strategy_unexpected_position_change",
                symbol=request.symbol,
                current_size=str(current_size),
                target_size=str(request.position_size),
                order_action=request.order_action
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to determine action for position change: {current_size} → {request.position_size}"
            )
        
        logger.info(
            "strategy_action_determined",
            symbol=request.symbol,
            action=action,
            side=side,
            quantity=str(quantity)
        )
        
        # Execute the determined action
        if action == "open":
            result = await trading_service.open_position(
                symbol=request.symbol,
                side=side,
                quantity=quantity,
                order_type=request.order_type,
                price=request.price
            )
            
            position_data = await position_service.get_position_by_symbol(request.symbol)
            
            return WebhookResponse(
                success=True,
                message=f"Position opened successfully for {request.symbol}",
                order=OrderResponse(**result) if result else None,
                position=PositionResponse(**position_data) if position_data else None
            )
        
        elif action == "close":
            result = await trading_service.close_position(symbol=request.symbol)
            
            return WebhookResponse(
                success=True,
                message=f"Position closed successfully for {request.symbol}",
                order=OrderResponse(**result["order"]) if result.get("order") else None,
                position=PositionResponse(**result["position"]) if result.get("position") else None
            )
        
        elif action == "increase":
            result = await trading_service.increase_position(
                symbol=request.symbol,
                quantity=quantity,
                order_type=request.order_type,
                price=request.price
            )
            
            return WebhookResponse(
                success=True,
                message=f"Position increased successfully for {request.symbol}",
                order=OrderResponse(**result["order"]) if result.get("order") else None,
                position=PositionResponse(**result["position"]) if result.get("position") else None
            )
        
        elif action == "decrease":
            result = await trading_service.decrease_position(
                symbol=request.symbol,
                quantity=quantity,
                order_type=request.order_type,
                price=request.price
            )
            
            return WebhookResponse(
                success=True,
                message=f"Position decreased successfully for {request.symbol}",
                order=OrderResponse(**result["order"]) if result.get("order") else None,
                position=PositionResponse(**result["position"]) if result.get("position") else None
            )
    
    except PositionNotFoundError as e:
        logger.error(
            "strategy_webhook_position_not_found",
            symbol=request.symbol,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except InvalidParameterError as e:
        logger.error(
            "strategy_webhook_invalid_parameter",
            symbol=request.symbol,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except AsterDEXClientError as e:
        logger.error(
            "strategy_webhook_asterdex_error",
            symbol=request.symbol,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AsterDEX API error: {str(e)}"
        )
    
    except Exception as e:
        logger.error(
            "strategy_webhook_unexpected_error",
            symbol=request.symbol,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
