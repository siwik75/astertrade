"""Response models for AsterDEX Trading API."""

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class OrderResponse(BaseModel):
    """Response model for order operations."""
    
    order_id: int = Field(..., description="Order ID", alias="orderId")
    symbol: str = Field(..., description="Trading pair symbol")
    side: str = Field(..., description="Order side: BUY or SELL")
    type: str = Field(..., description="Order type")
    status: str = Field(..., description="Order status")
    quantity: Decimal = Field(..., description="Order quantity", alias="origQty")
    price: Optional[Decimal] = Field(None, description="Order price")
    executed_qty: Decimal = Field(
        ...,
        description="Executed quantity",
        alias="executedQty"
    )
    avg_price: Optional[Decimal] = Field(
        None,
        description="Average execution price",
        alias="avgPrice"
    )
    time_in_force: Optional[str] = Field(
        None,
        description="Time in force",
        alias="timeInForce"
    )
    position_side: Optional[str] = Field(
        None,
        description="Position side",
        alias="positionSide"
    )
    reduce_only: Optional[bool] = Field(
        None,
        description="Reduce only flag",
        alias="reduceOnly"
    )
    close_position: Optional[bool] = Field(
        None,
        description="Close position flag",
        alias="closePosition"
    )
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "examples": [
                {
                    "orderId": 123456789,
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "type": "MARKET",
                    "status": "FILLED",
                    "origQty": "0.001",
                    "executedQty": "0.001",
                    "avgPrice": "50000.00"
                }
            ]
        }
    }


class PositionResponse(BaseModel):
    """Response model for position information."""
    
    symbol: str = Field(..., description="Trading pair symbol")
    position_side: str = Field(
        ...,
        description="Position side: BOTH, LONG, or SHORT",
        alias="positionSide"
    )
    position_amt: Decimal = Field(
        ...,
        description="Position amount",
        alias="positionAmt"
    )
    entry_price: Decimal = Field(
        ...,
        description="Average entry price",
        alias="entryPrice"
    )
    mark_price: Decimal = Field(
        ...,
        description="Current mark price",
        alias="markPrice"
    )
    unrealized_profit: Decimal = Field(
        ...,
        description="Unrealized profit/loss",
        alias="unRealizedProfit"
    )
    leverage: int = Field(..., description="Current leverage")
    margin_type: str = Field(
        ...,
        description="Margin type: ISOLATED or CROSSED",
        alias="marginType"
    )
    liquidation_price: Decimal = Field(
        ...,
        description="Liquidation price",
        alias="liquidationPrice"
    )
    isolated_margin: Optional[Decimal] = Field(
        None,
        description="Isolated margin",
        alias="isolatedMargin"
    )
    notional: Optional[Decimal] = Field(
        None,
        description="Position notional value"
    )
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "BTCUSDT",
                    "positionSide": "BOTH",
                    "positionAmt": "0.001",
                    "entryPrice": "50000.00",
                    "markPrice": "51000.00",
                    "unRealizedProfit": "1.00",
                    "leverage": 10,
                    "marginType": "CROSSED",
                    "liquidationPrice": "45000.00"
                }
            ]
        }
    }


class BalanceResponse(BaseModel):
    """Response model for account balance."""
    
    asset: str = Field(..., description="Asset name (e.g., USDT)")
    balance: Decimal = Field(
        ...,
        description="Total wallet balance"
    )
    available_balance: Decimal = Field(
        ...,
        description="Available balance for trading",
        alias="availableBalance"
    )
    cross_wallet_balance: Decimal = Field(
        ...,
        description="Cross wallet balance",
        alias="crossWalletBalance"
    )
    cross_un_pnl: Decimal = Field(
        ...,
        description="Cross unrealized PnL",
        alias="crossUnPnl"
    )
    max_withdraw_amount: Optional[Decimal] = Field(
        None,
        description="Maximum amount for transfer out",
        alias="maxWithdrawAmount"
    )
    margin_available: Optional[bool] = Field(
        None,
        description="Whether the asset can be used as margin",
        alias="marginAvailable"
    )
    update_time: Optional[int] = Field(
        None,
        description="Update timestamp",
        alias="updateTime"
    )
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "examples": [
                {
                    "asset": "USDT",
                    "walletBalance": "10000.00",
                    "availableBalance": "9500.00",
                    "crossWalletBalance": "10000.00",
                    "unrealizedProfit": "50.00"
                }
            ]
        }
    }


class WebhookResponse(BaseModel):
    """Response model for webhook requests."""
    
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Response message")
    order: Optional[OrderResponse] = Field(
        None,
        description="Order information if applicable"
    )
    position: Optional[PositionResponse] = Field(
        None,
        description="Position information if applicable"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Position opened successfully",
                    "order": {
                        "orderId": 123456789,
                        "symbol": "BTCUSDT",
                        "side": "BUY",
                        "type": "MARKET",
                        "status": "FILLED",
                        "origQty": "0.001",
                        "executedQty": "0.001",
                        "avgPrice": "50000.00"
                    }
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Response model for error responses."""
    
    error: str = Field(..., description="Error type/category")
    detail: str = Field(..., description="Detailed error information")
    code: Optional[str] = Field(None, description="Application-specific error code")
    timestamp: int = Field(..., description="Error timestamp in milliseconds")
    original_error_code: Optional[int] = Field(
        None,
        description="Original error code from AsterDEX API",
        alias="originalErrorCode"
    )
    original_error_message: Optional[str] = Field(
        None,
        description="Original error message from AsterDEX API",
        alias="originalErrorMessage"
    )
    validation_errors: Optional[list] = Field(
        None,
        description="List of validation errors",
        alias="validationErrors"
    )
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "examples": [
                {
                    "error": "PositionNotFound",
                    "detail": "No open position for symbol BTCUSDT",
                    "code": "POSITION_NOT_FOUND",
                    "timestamp": 1699999999999
                },
                {
                    "error": "ValidationError",
                    "detail": "Request validation failed",
                    "code": "VALIDATION_ERROR",
                    "timestamp": 1699999999999,
                    "validationErrors": [
                        {
                            "field": "quantity",
                            "message": "Quantity must be positive",
                            "type": "value_error"
                        }
                    ]
                },
                {
                    "error": "ExternalAPIError",
                    "detail": "AsterDEX API error: Insufficient balance",
                    "code": "EXTERNAL_API_ERROR",
                    "timestamp": 1699999999999,
                    "originalErrorCode": -2019,
                    "originalErrorMessage": "Margin is insufficient"
                }
            ]
        }
    }
