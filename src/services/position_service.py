"""Position service for querying and managing positions."""

from decimal import Decimal
from typing import List, Dict, Any, Optional

from ..client.asterdex_client import AsterDEXClient, AsterDEXClientError
from ..logging_config import get_logger


logger = get_logger(__name__)


class PositionServiceError(Exception):
    """Base exception for position service errors."""
    pass


class InvalidLeverageError(PositionServiceError):
    """Raised when invalid leverage value is provided."""
    pass


class InvalidMarginTypeError(PositionServiceError):
    """Raised when invalid margin type is provided."""
    pass


class PositionService:
    """
    Service for position management operations.
    
    Handles:
    - Querying positions
    - Updating leverage
    - Updating margin type
    """
    
    def __init__(self, client: AsterDEXClient):
        """
        Initialize position service.
        
        Args:
            client: AsterDEX API client
        """
        self.client = client
    
    async def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all positions or positions for a specific symbol.
        
        Filters out positions with zero position amount.
        
        Args:
            symbol: Optional trading pair symbol to filter
            
        Returns:
            List of position dictionaries with non-zero amounts
            
        Raises:
            AsterDEXClientError: If API request fails
        """
        logger.info("getting_positions", symbol=symbol)
        
        try:
            # Get position risk from API
            positions = await self.client.get_position_risk(symbol)
            
            # Filter out zero positions
            non_zero_positions = []
            for pos in positions:
                position_amt = Decimal(str(pos.get("positionAmt", "0")))
                if position_amt != 0:
                    non_zero_positions.append(pos)
            
            logger.info(
                "positions_retrieved",
                symbol=symbol,
                total_positions=len(positions),
                non_zero_positions=len(non_zero_positions)
            )
            
            return non_zero_positions
            
        except AsterDEXClientError as e:
            logger.error(
                "failed_to_get_positions",
                symbol=symbol,
                error=str(e)
            )
            raise
    
    async def get_position_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get position for a specific symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Position dictionary if found, None otherwise
            
        Raises:
            AsterDEXClientError: If API request fails
        """
        logger.info("getting_position_by_symbol", symbol=symbol)
        
        try:
            # Get positions for symbol
            positions = await self.get_positions(symbol)
            
            # Return first non-zero position or None
            if positions:
                logger.info("position_found", symbol=symbol)
                return positions[0]
            else:
                logger.info("position_not_found", symbol=symbol)
                return None
                
        except AsterDEXClientError as e:
            logger.error(
                "failed_to_get_position_by_symbol",
                symbol=symbol,
                error=str(e)
            )
            raise
    
    async def update_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """
        Update leverage for a symbol.
        
        Args:
            symbol: Trading pair symbol
            leverage: Leverage value (1-125)
            
        Returns:
            Leverage update confirmation from API
            
        Raises:
            InvalidLeverageError: If leverage is out of valid range
            AsterDEXClientError: If API request fails
        """
        # Validate leverage range
        if not isinstance(leverage, int) or leverage < 1 or leverage > 125:
            raise InvalidLeverageError(
                f"Leverage must be an integer between 1 and 125, got {leverage}"
            )
        
        logger.info(
            "updating_leverage",
            symbol=symbol,
            leverage=leverage
        )
        
        try:
            # Call API to change leverage
            result = await self.client.change_leverage(symbol, leverage)
            
            logger.info(
                "leverage_updated",
                symbol=symbol,
                leverage=leverage
            )
            
            return result
            
        except AsterDEXClientError as e:
            logger.error(
                "failed_to_update_leverage",
                symbol=symbol,
                leverage=leverage,
                error=str(e)
            )
            raise
    
    async def update_margin_type(self, symbol: str, margin_type: str) -> Dict[str, Any]:
        """
        Update margin type for a symbol.
        
        Args:
            symbol: Trading pair symbol
            margin_type: Margin type (ISOLATED or CROSSED)
            
        Returns:
            Margin type update confirmation from API
            
        Raises:
            InvalidMarginTypeError: If margin type is invalid
            AsterDEXClientError: If API request fails
        """
        # Validate margin type
        margin_type_upper = margin_type.upper()
        if margin_type_upper not in ("ISOLATED", "CROSSED"):
            raise InvalidMarginTypeError(
                f"Margin type must be ISOLATED or CROSSED, got {margin_type}"
            )
        
        logger.info(
            "updating_margin_type",
            symbol=symbol,
            margin_type=margin_type_upper
        )
        
        try:
            # Call API to change margin type
            result = await self.client.change_margin_type(symbol, margin_type_upper)
            
            logger.info(
                "margin_type_updated",
                symbol=symbol,
                margin_type=margin_type_upper
            )
            
            return result
            
        except AsterDEXClientError as e:
            logger.error(
                "failed_to_update_margin_type",
                symbol=symbol,
                margin_type=margin_type_upper,
                error=str(e)
            )
            raise
