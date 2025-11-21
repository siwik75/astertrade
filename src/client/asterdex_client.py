"""AsterDEX HTTP client for API communication"""

import time
import asyncio
from typing import Dict, Any, Optional, List
from decimal import Decimal
import httpx

from .authenticator import AsterDEXAuthenticator
from ..logging_config import get_logger


logger = get_logger(__name__)


class AsterDEXClientError(Exception):
    """Base exception for AsterDEX client errors"""
    pass


class RateLimitError(AsterDEXClientError):
    """Raised when rate limit is exceeded"""
    pass


class ServerError(AsterDEXClientError):
    """Raised when server returns 5xx error"""
    pass


class AsterDEXClient:
    """
    Async HTTP client for AsterDEX Futures API v3.
    
    Features:
    - Connection pooling with httpx
    - Automatic authentication for protected endpoints
    - Retry logic for rate limits (429) and server errors (5xx)
    - Exponential backoff for retries
    """
    
    def __init__(
        self,
        base_url: str,
        authenticator: AsterDEXAuthenticator,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_retry_delay: int = 2
    ):
        """
        Initialize AsterDEX client.
        
        Args:
            base_url: Base URL for AsterDEX API
            authenticator: Authentication handler
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            rate_limit_retry_delay: Base delay for rate limit retries
        """
        self.base_url = base_url.rstrip('/')
        self.auth = authenticator
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_retry_delay = rate_limit_retry_delay
        
        # Create async HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
        )
    
    async def close(self):
        """Close HTTP client and cleanup connections"""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    def _add_timestamp_and_recv_window(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add timestamp and recvWindow to request parameters.
        
        Args:
            params: Request parameters
            
        Returns:
            Parameters with timestamp and recvWindow added
        """
        params = params.copy()
        params['timestamp'] = int(time.time() * 1000)  # milliseconds
        params['recvWindow'] = 5000  # 5 seconds
        return params

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        requires_auth: bool = True
    ) -> Any:
        """
        Make HTTP request to AsterDEX API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint path
            params: Request parameters
            requires_auth: Whether authentication is required
            
        Returns:
            Parsed JSON response
            
        Raises:
            RateLimitError: When rate limit exceeded after retries
            ServerError: When server error persists after retries
            AsterDEXClientError: For other API errors
        """
        if params is None:
            params = {}
        
        url = f"{self.base_url}{endpoint}"
        
        # Add timestamp and recvWindow for authenticated requests
        if requires_auth:
            params = self._add_timestamp_and_recv_window(params)
            params = self.auth.add_auth_params(params)
        
        # Retry loop with exponential backoff
        for attempt in range(self.max_retries + 1):
            try:
                # Log request
                logger.info(
                    "asterdex_api_request",
                    method=method,
                    endpoint=endpoint,
                    attempt=attempt + 1,
                    requires_auth=requires_auth
                )
                
                # Make request based on method
                if method.upper() == "GET":
                    response = await self.client.get(url, params=params)
                elif method.upper() == "POST":
                    response = await self.client.post(url, params=params)
                elif method.upper() == "DELETE":
                    response = await self.client.delete(url, params=params)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Handle rate limit (429)
                if response.status_code == 429:
                    if attempt < self.max_retries:
                        delay = self.rate_limit_retry_delay * (2 ** attempt)
                        logger.warning(
                            "rate_limit_exceeded",
                            attempt=attempt + 1,
                            retry_delay=delay
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise RateLimitError("Rate limit exceeded after maximum retries")
                
                # Handle server errors (5xx)
                if 500 <= response.status_code < 600:
                    if attempt < self.max_retries:
                        delay = self.rate_limit_retry_delay * (2 ** attempt)
                        logger.warning(
                            "server_error",
                            status_code=response.status_code,
                            attempt=attempt + 1,
                            retry_delay=delay
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise ServerError(
                            f"Server error {response.status_code} after maximum retries"
                        )
                
                # Handle client errors (4xx except 429)
                if 400 <= response.status_code < 500:
                    error_data = response.json() if response.text else {}
                    error_code = error_data.get("code") if isinstance(error_data, dict) else None
                    error_msg = error_data.get("msg") if isinstance(error_data, dict) else str(error_data)
                    
                    logger.error(
                        "client_error",
                        status_code=response.status_code,
                        error_code=error_code,
                        error_message=error_msg,
                        error_data=error_data
                    )
                    
                    # Create detailed error message
                    if error_code and error_msg:
                        error_detail = f"AsterDEX error {error_code}: {error_msg}"
                    else:
                        error_detail = f"Client error {response.status_code}: {error_data}"
                    
                    raise AsterDEXClientError(error_detail)
                
                # Success - parse and return response
                response.raise_for_status()
                
                # Validate response is valid JSON
                try:
                    result = response.json()
                except Exception as e:
                    logger.error(
                        "invalid_json_response",
                        status_code=response.status_code,
                        response_text=response.text[:200],
                        error=str(e)
                    )
                    raise AsterDEXClientError(
                        f"Invalid JSON response from AsterDEX API: {str(e)}"
                    )
                
                # Validate response structure for error responses
                if isinstance(result, dict) and "code" in result and "msg" in result:
                    # This looks like an error response even though status is 200
                    error_code = result.get("code")
                    error_msg = result.get("msg")
                    logger.warning(
                        "error_in_success_response",
                        error_code=error_code,
                        error_message=error_msg
                    )
                    raise AsterDEXClientError(
                        f"AsterDEX error {error_code}: {error_msg}"
                    )
                
                logger.info(
                    "asterdex_api_response",
                    method=method,
                    endpoint=endpoint,
                    status_code=response.status_code
                )
                
                return result
                
            except httpx.TimeoutException as e:
                if attempt < self.max_retries:
                    delay = self.rate_limit_retry_delay * (2 ** attempt)
                    logger.warning(
                        "request_timeout",
                        attempt=attempt + 1,
                        retry_delay=delay
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error("request_timeout_final", error=str(e))
                    raise AsterDEXClientError(f"Request timeout after {self.max_retries} retries")
            
            except httpx.HTTPError as e:
                if attempt < self.max_retries:
                    delay = self.rate_limit_retry_delay * (2 ** attempt)
                    logger.warning(
                        "http_error",
                        error=str(e),
                        attempt=attempt + 1,
                        retry_delay=delay
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error("http_error_final", error=str(e))
                    raise AsterDEXClientError(f"HTTP error: {str(e)}")
        
        # Should not reach here, but just in case
        raise AsterDEXClientError("Maximum retries exceeded")

    # Trading Endpoints
    
    async def create_order(self, order_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new order.
        
        POST /fapi/v3/order
        
        Args:
            order_params: Order parameters including:
                - symbol: Trading pair (e.g., BTCUSDT)
                - side: BUY or SELL
                - type: Order type (MARKET, LIMIT, etc.)
                - quantity: Order quantity
                - price: Price (for limit orders)
                - timeInForce: Time in force (for limit orders)
                - positionSide: BOTH, LONG, or SHORT
                - reduceOnly: True/False
                - closePosition: True/False
                
        Returns:
            Order response with orderId, status, etc.
        """
        return await self._request("POST", "/fapi/v3/order", params=order_params)
    
    async def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Cancel an active order.
        
        DELETE /fapi/v3/order
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID to cancel
            
        Returns:
            Cancellation confirmation
        """
        params = {
            "symbol": symbol,
            "orderId": order_id
        }
        return await self._request("DELETE", "/fapi/v3/order", params=params)
    
    async def get_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Query order status.
        
        GET /fapi/v3/order
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID to query
            
        Returns:
            Order details
        """
        params = {
            "symbol": symbol,
            "orderId": order_id
        }
        return await self._request("GET", "/fapi/v3/order", params=params)
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open orders.
        
        GET /fapi/v3/openOrders
        
        Args:
            symbol: Optional trading pair symbol to filter
            
        Returns:
            List of open orders
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        return await self._request("GET", "/fapi/v3/openOrders", params=params)
    
    async def get_all_orders(
        self,
        symbol: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all orders (active, canceled, filled).
        
        GET /fapi/v3/allOrders
        
        Args:
            symbol: Trading pair symbol
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            limit: Number of orders to return (default 50, max 1000)
            
        Returns:
            List of orders
        """
        params = {
            "symbol": symbol,
            "limit": limit
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        return await self._request("GET", "/fapi/v3/allOrders", params=params)

    # Position Endpoints
    
    async def get_position_risk(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get current position information.
        
        GET /fapi/v3/positionRisk
        
        Args:
            symbol: Optional trading pair symbol to filter
            
        Returns:
            List of position information
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        return await self._request("GET", "/fapi/v3/positionRisk", params=params)
    
    async def change_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """
        Change leverage for a symbol.
        
        POST /fapi/v3/leverage
        
        Args:
            symbol: Trading pair symbol
            leverage: Leverage value (1-125)
            
        Returns:
            Leverage change confirmation
        """
        params = {
            "symbol": symbol,
            "leverage": leverage
        }
        return await self._request("POST", "/fapi/v3/leverage", params=params)
    
    async def change_margin_type(self, symbol: str, margin_type: str) -> Dict[str, Any]:
        """
        Change margin type for a symbol.
        
        POST /fapi/v3/marginType
        
        Args:
            symbol: Trading pair symbol
            margin_type: ISOLATED or CROSSED
            
        Returns:
            Margin type change confirmation
        """
        params = {
            "symbol": symbol,
            "marginType": margin_type
        }
        return await self._request("POST", "/fapi/v3/marginType", params=params)
    
    # Account Endpoints
    
    async def get_account_balance(self) -> List[Dict[str, Any]]:
        """
        Get account balance information.
        
        GET /fapi/v3/balance
        
        Returns:
            List of asset balances
        """
        return await self._request("GET", "/fapi/v3/balance", params={})
    
    async def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information including positions and balances.
        
        GET /fapi/v3/account
        
        Returns:
            Account information
        """
        return await self._request("GET", "/fapi/v3/account", params={})

    # Market Data Endpoints (no authentication required)
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange trading rules and symbol information.
        
        GET /fapi/v3/exchangeInfo
        
        No authentication required.
        
        Returns:
            Exchange information including symbols, trading rules, etc.
        """
        return await self._request("GET", "/fapi/v3/exchangeInfo", params={}, requires_auth=False)
    
    async def get_ticker_price(self, symbol: Optional[str] = None) -> Any:
        """
        Get latest price for a symbol or all symbols.
        
        GET /fapi/v3/ticker/price
        
        No authentication required.
        
        Args:
            symbol: Optional trading pair symbol
            
        Returns:
            Price ticker(s) - single dict if symbol provided, list otherwise
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        return await self._request("GET", "/fapi/v3/ticker/price", params=params, requires_auth=False)
