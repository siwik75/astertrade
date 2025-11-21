"""Trading service for position management operations."""

from decimal import Decimal
from typing import Dict, Any, Optional

from ..client.asterdex_client import AsterDEXClient, AsterDEXClientError
from ..logging_config import get_logger


logger = get_logger(__name__)


class TradingServiceError(Exception):
    """Base exception for trading service errors."""
    pass


class PositionNotFoundError(TradingServiceError):
    """Raised when a position is not found."""
    pass


class InvalidParameterError(TradingServiceError):
    """Raised when invalid parameters are provided."""
    pass


class TradingService:
    """
    Service for executing trading operations.
    
    Handles:
    - Opening new positions
    - Increasing existing positions
    - Decreasing positions (partial close)
    - Closing entire positions
    """
    
    def __init__(self, client: AsterDEXClient):
        """
        Initialize trading service.
        
        Args:
            client: AsterDEX API client
        """
        self.client = client
    
    def _validate_symbol(self, symbol: str) -> None:
        """
        Validate symbol parameter.
        
        Args:
            symbol: Trading pair symbol
            
        Raises:
            InvalidParameterError: If symbol is invalid
        """
        if not symbol or not isinstance(symbol, str):
            raise InvalidParameterError("Symbol must be a non-empty string")
        if not symbol.isupper():
            raise InvalidParameterError("Symbol must be uppercase (e.g., BTCUSDT)")
    
    def _validate_side(self, side: str) -> None:
        """
        Validate side parameter.
        
        Args:
            side: Order side (BUY or SELL)
            
        Raises:
            InvalidParameterError: If side is invalid
        """
        if side not in ("BUY", "SELL"):
            raise InvalidParameterError("Side must be either BUY or SELL")
    
    def _validate_quantity(self, quantity: Decimal) -> None:
        """
        Validate quantity parameter.
        
        Args:
            quantity: Order quantity
            
        Raises:
            InvalidParameterError: If quantity is invalid
        """
        if quantity <= 0:
            raise InvalidParameterError("Quantity must be positive")
    
    def _validate_price(self, price: Optional[Decimal]) -> None:
        """
        Validate price parameter.
        
        Args:
            price: Order price
            
        Raises:
            InvalidParameterError: If price is invalid
        """
        if price is not None and price <= 0:
            raise InvalidParameterError("Price must be positive")

    async def open_position(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        order_type: str = "MARKET",
        price: Optional[Decimal] = None,
        position_side: str = "BOTH"
    ) -> Dict[str, Any]:
        """
        Open a new position.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            side: Order side (BUY or SELL)
            quantity: Order quantity
            order_type: Order type (MARKET or LIMIT)
            price: Limit order price (required for LIMIT orders)
            position_side: Position side (BOTH, LONG, or SHORT)
            
        Returns:
            Order response from AsterDEX API
            
        Raises:
            InvalidParameterError: If parameters are invalid
            AsterDEXClientError: If API request fails
        """
        # Validate parameters
        self._validate_symbol(symbol)
        self._validate_side(side)
        self._validate_quantity(quantity)
        self._validate_price(price)
        
        # Build order parameters
        order_params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
            "positionSide": position_side
        }
        
        # Add price and timeInForce for limit orders
        if order_type == "LIMIT":
            if price is None:
                raise InvalidParameterError("Price is required for LIMIT orders")
            order_params["price"] = str(price)
            order_params["timeInForce"] = "GTC"  # Good Till Cancel
        
        logger.info(
            "opening_position",
            symbol=symbol,
            side=side,
            quantity=str(quantity),
            order_type=order_type
        )
        
        try:
            # Execute order via client
            result = await self.client.create_order(order_params)
            
            logger.info(
                "position_opened",
                symbol=symbol,
                order_id=result.get("orderId"),
                status=result.get("status")
            )
            
            return result
            
        except AsterDEXClientError as e:
            logger.error(
                "failed_to_open_position",
                symbol=symbol,
                error=str(e)
            )
            raise
    
    async def increase_position(
        self,
        symbol: str,
        quantity: Decimal,
        order_type: str = "MARKET",
        price: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Increase an existing position.
        
        Queries the current position to determine the side, then places
        an additional order in the same direction.
        
        Args:
            symbol: Trading pair symbol
            quantity: Additional quantity to add
            order_type: Order type (MARKET or LIMIT)
            price: Limit order price (required for LIMIT orders)
            
        Returns:
            Dict containing order and updated position information
            
        Raises:
            PositionNotFoundError: If no position exists for the symbol
            InvalidParameterError: If parameters are invalid
            AsterDEXClientError: If API request fails
        """
        # Validate parameters
        self._validate_symbol(symbol)
        self._validate_quantity(quantity)
        self._validate_price(price)
        
        logger.info(
            "increasing_position",
            symbol=symbol,
            quantity=str(quantity)
        )
        
        try:
            # Get current position
            positions = await self.client.get_position_risk(symbol)
            
            # Find non-zero position
            current_position = None
            for pos in positions:
                position_amt = Decimal(str(pos.get("positionAmt", "0")))
                if position_amt != 0:
                    current_position = pos
                    break
            
            if current_position is None:
                raise PositionNotFoundError(
                    f"No open position found for symbol {symbol}"
                )
            
            # Determine side from position amount
            position_amt = Decimal(str(current_position["positionAmt"]))
            side = "BUY" if position_amt > 0 else "SELL"
            position_side = current_position.get("positionSide", "BOTH")
            
            logger.info(
                "current_position_found",
                symbol=symbol,
                position_amt=str(position_amt),
                side=side
            )
            
            # Place order in same direction
            order_result = await self.open_position(
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type=order_type,
                price=price,
                position_side=position_side
            )
            
            # Get updated position
            updated_positions = await self.client.get_position_risk(symbol)
            updated_position = None
            for pos in updated_positions:
                if Decimal(str(pos.get("positionAmt", "0"))) != 0:
                    updated_position = pos
                    break
            
            return {
                "order": order_result,
                "position": updated_position
            }
            
        except PositionNotFoundError:
            raise
        except AsterDEXClientError as e:
            logger.error(
                "failed_to_increase_position",
                symbol=symbol,
                error=str(e)
            )
            raise
    
    async def decrease_position(
        self,
        symbol: str,
        quantity: Decimal,
        order_type: str = "MARKET",
        price: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Decrease an existing position (partial close).
        
        Places a reduce-only order in the opposite direction to reduce
        the position size.
        
        Args:
            symbol: Trading pair symbol
            quantity: Quantity to reduce
            order_type: Order type (MARKET or LIMIT)
            price: Limit order price (required for LIMIT orders)
            
        Returns:
            Dict containing order and updated position information
            
        Raises:
            PositionNotFoundError: If no position exists for the symbol
            InvalidParameterError: If quantity exceeds position size
            AsterDEXClientError: If API request fails
        """
        # Validate parameters
        self._validate_symbol(symbol)
        self._validate_quantity(quantity)
        self._validate_price(price)
        
        logger.info(
            "decreasing_position",
            symbol=symbol,
            quantity=str(quantity)
        )
        
        try:
            # Get current position
            positions = await self.client.get_position_risk(symbol)
            
            # Find non-zero position
            current_position = None
            for pos in positions:
                position_amt = Decimal(str(pos.get("positionAmt", "0")))
                if position_amt != 0:
                    current_position = pos
                    break
            
            if current_position is None:
                raise PositionNotFoundError(
                    f"No open position found for symbol {symbol}"
                )
            
            # Validate quantity doesn't exceed position
            position_amt = Decimal(str(current_position["positionAmt"]))
            abs_position_amt = abs(position_amt)
            
            if quantity > abs_position_amt:
                raise InvalidParameterError(
                    f"Decrease quantity {quantity} exceeds position size {abs_position_amt}"
                )
            
            # Determine opposite side for reduce-only order
            side = "SELL" if position_amt > 0 else "BUY"
            position_side = current_position.get("positionSide", "BOTH")
            
            logger.info(
                "placing_reduce_order",
                symbol=symbol,
                side=side,
                quantity=str(quantity)
            )
            
            # Build reduce-only order parameters
            order_params = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": str(quantity),
                "positionSide": position_side,
                "reduceOnly": "true"
            }
            
            # Add price and timeInForce for limit orders
            if order_type == "LIMIT":
                if price is None:
                    raise InvalidParameterError("Price is required for LIMIT orders")
                order_params["price"] = str(price)
                order_params["timeInForce"] = "GTC"
            
            # Execute reduce-only order
            order_result = await self.client.create_order(order_params)
            
            logger.info(
                "position_decreased",
                symbol=symbol,
                order_id=order_result.get("orderId")
            )
            
            # Get updated position
            updated_positions = await self.client.get_position_risk(symbol)
            updated_position = None
            for pos in updated_positions:
                if pos.get("symbol") == symbol:
                    updated_position = pos
                    break
            
            return {
                "order": order_result,
                "position": updated_position
            }
            
        except (PositionNotFoundError, InvalidParameterError):
            raise
        except AsterDEXClientError as e:
            logger.error(
                "failed_to_decrease_position",
                symbol=symbol,
                error=str(e)
            )
            raise
    
    async def close_position(self, symbol: str) -> Dict[str, Any]:
        """
        Close an entire position.
        
        Places a market order with closePosition flag to close the
        entire position for the symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Dict containing order result and final position info
            
        Raises:
            PositionNotFoundError: If no position exists for the symbol
            AsterDEXClientError: If API request fails
        """
        # Validate parameters
        self._validate_symbol(symbol)
        
        logger.info("closing_position", symbol=symbol)
        
        try:
            # Get current position
            positions = await self.client.get_position_risk(symbol)
            
            # Find non-zero position
            current_position = None
            for pos in positions:
                position_amt = Decimal(str(pos.get("positionAmt", "0")))
                if position_amt != 0:
                    current_position = pos
                    break
            
            if current_position is None:
                raise PositionNotFoundError(
                    f"No open position found for symbol {symbol}"
                )
            
            # Determine side and position_side
            position_amt = Decimal(str(current_position["positionAmt"]))
            side = "SELL" if position_amt > 0 else "BUY"
            position_side = current_position.get("positionSide", "BOTH")
            
            logger.info(
                "closing_position_details",
                symbol=symbol,
                position_amt=str(position_amt),
                side=side
            )
            
            # Build close position order parameters
            order_params = {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "positionSide": position_side,
                "closePosition": "true"
            }
            
            # Execute close position order
            order_result = await self.client.create_order(order_params)
            
            logger.info(
                "position_closed",
                symbol=symbol,
                order_id=order_result.get("orderId")
            )
            
            # Get final position (should be zero)
            final_positions = await self.client.get_position_risk(symbol)
            final_position = None
            for pos in final_positions:
                if pos.get("symbol") == symbol:
                    final_position = pos
                    break
            
            return {
                "order": order_result,
                "position": final_position,
                "closed": True
            }
            
        except PositionNotFoundError:
            raise
        except AsterDEXClientError as e:
            logger.error(
                "failed_to_close_position",
                symbol=symbol,
                error=str(e)
            )
            raise
