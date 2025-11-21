"""Request models for AsterDEX Trading API."""

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class WebhookRequest(BaseModel):
    """TradingView webhook request model."""
    
    action: str = Field(
        ...,
        description="Trading action to perform",
        examples=["open", "increase", "decrease", "close"]
    )
    symbol: str = Field(
        ...,
        description="Trading pair symbol (e.g., BTCUSDT)",
        examples=["BTCUSDT", "ETHUSDT"]
    )
    side: Optional[str] = Field(
        None,
        description="Order side: BUY or SELL (required for open action)",
        examples=["BUY", "SELL"]
    )
    quantity: Optional[Decimal] = Field(
        None,
        description="Order quantity (required for open, increase, decrease)",
        examples=["0.001", "1.5"]
    )
    price: Optional[Decimal] = Field(
        None,
        description="Limit order price (optional, for limit orders only)",
        examples=["50000.00", "3000.50"]
    )
    order_type: str = Field(
        "MARKET",
        description="Order type: MARKET or LIMIT",
        examples=["MARKET", "LIMIT"]
    )
    webhook_secret: Optional[str] = Field(
        None,
        description="Optional webhook secret for authentication (can be provided in body or header)",
        examples=["your-secret-token-here"]
    )
    
    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        """Validate action is one of the supported values."""
        allowed_actions = {"open", "increase", "decrease", "close"}
        if v.lower() not in allowed_actions:
            raise ValueError(
                f"Action must be one of {allowed_actions}, got '{v}'"
            )
        return v.lower()
    
    @field_validator("side")
    @classmethod
    def validate_side(cls, v: Optional[str]) -> Optional[str]:
        """Validate side is BUY or SELL."""
        if v is None:
            return v
        allowed_sides = {"BUY", "SELL"}
        v_upper = v.upper()
        if v_upper not in allowed_sides:
            raise ValueError(
                f"Side must be one of {allowed_sides}, got '{v}'"
            )
        return v_upper
    
    @field_validator("order_type")
    @classmethod
    def validate_order_type(cls, v: str) -> str:
        """Validate order type is MARKET or LIMIT."""
        allowed_types = {"MARKET", "LIMIT"}
        v_upper = v.upper()
        if v_upper not in allowed_types:
            raise ValueError(
                f"Order type must be one of {allowed_types}, got '{v}'"
            )
        return v_upper
    
    @field_validator("quantity", "price")
    @classmethod
    def validate_positive(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Validate quantity and price are positive."""
        if v is not None and v <= 0:
            raise ValueError("Value must be positive")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "action": "open",
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "quantity": "0.001",
                    "order_type": "MARKET"
                },
                {
                    "action": "open",
                    "symbol": "ETHUSDT",
                    "side": "SELL",
                    "quantity": "0.5",
                    "price": "3000.00",
                    "order_type": "LIMIT"
                },
                {
                    "action": "increase",
                    "symbol": "BTCUSDT",
                    "quantity": "0.001"
                },
                {
                    "action": "close",
                    "symbol": "BTCUSDT"
                }
            ]
        }
    }


class LeverageUpdateRequest(BaseModel):
    """Request model for updating position leverage."""
    
    leverage: int = Field(
        ...,
        ge=1,
        le=125,
        description="Leverage value between 1 and 125",
        examples=[10, 20, 50, 100]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {"leverage": 10},
                {"leverage": 50},
                {"leverage": 125}
            ]
        }
    }


class MarginTypeUpdateRequest(BaseModel):
    """Request model for updating position margin type."""
    
    margin_type: str = Field(
        ...,
        description="Margin type: ISOLATED or CROSSED",
        examples=["ISOLATED", "CROSSED"]
    )
    
    @field_validator("margin_type")
    @classmethod
    def validate_margin_type(cls, v: str) -> str:
        """Validate margin type is ISOLATED or CROSSED."""
        allowed_types = {"ISOLATED", "CROSSED"}
        v_upper = v.upper()
        if v_upper not in allowed_types:
            raise ValueError(
                f"Margin type must be one of {allowed_types}, got '{v}'"
            )
        return v_upper
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {"margin_type": "ISOLATED"},
                {"margin_type": "CROSSED"}
            ]
        }
    }


class StrategyWebhookRequest(BaseModel):
    """TradingView strategy webhook request model.
    
    This model handles TradingView strategy orders and automatically
    determines the correct action (open/close/increase/decrease) based
    on the order flow and current position.
    """
    
    order_action: str = Field(
        ...,
        description="Strategy order action: buy or sell",
        examples=["buy", "sell"]
    )
    symbol: str = Field(
        ...,
        description="Trading pair symbol (e.g., BTCUSDT)",
        examples=["BTCUSDT", "ETHUSDT"]
    )
    contracts: Decimal = Field(
        ...,
        description="Number of contracts from strategy order",
        examples=["0.575181", "0.001"]
    )
    position_size: Decimal = Field(
        ...,
        description="Strategy position size after this order",
        examples=["0.575181", "-0.30691", "0"]
    )
    order_type: str = Field(
        "MARKET",
        description="Order type: MARKET or LIMIT",
        examples=["MARKET", "LIMIT"]
    )
    price: Optional[Decimal] = Field(
        None,
        description="Limit order price (optional, for limit orders only)",
        examples=["50000.00", "3000.50"]
    )
    webhook_secret: Optional[str] = Field(
        None,
        description="Optional webhook secret for authentication (can be provided in body or header)",
        examples=["your-secret-token-here"]
    )
    
    @field_validator("order_action")
    @classmethod
    def validate_order_action(cls, v: str) -> str:
        """Validate order action is buy or sell."""
        allowed_actions = {"buy", "sell"}
        v_lower = v.lower()
        if v_lower not in allowed_actions:
            raise ValueError(
                f"Order action must be one of {allowed_actions}, got '{v}'"
            )
        return v_lower
    
    @field_validator("order_type")
    @classmethod
    def validate_order_type(cls, v: str) -> str:
        """Validate order type is MARKET or LIMIT."""
        allowed_types = {"MARKET", "LIMIT"}
        v_upper = v.upper()
        if v_upper not in allowed_types:
            raise ValueError(
                f"Order type must be one of {allowed_types}, got '{v}'"
            )
        return v_upper
    
    @field_validator("contracts")
    @classmethod
    def validate_contracts(cls, v: Decimal) -> Decimal:
        """Validate contracts is positive."""
        if v <= 0:
            raise ValueError("Contracts must be positive")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "order_action": "buy",
                    "symbol": "BTCUSDT",
                    "contracts": "0.575181",
                    "position_size": "0.575181",
                    "order_type": "MARKET"
                },
                {
                    "order_action": "sell",
                    "symbol": "BTCUSDT",
                    "contracts": "0.30691",
                    "position_size": "0",
                    "order_type": "MARKET"
                }
            ]
        }
    }
