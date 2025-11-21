"""Account service for balance and account information."""

import time
from typing import List, Dict, Any, Optional

from ..client.asterdex_client import AsterDEXClient, AsterDEXClientError
from ..logging_config import get_logger


logger = get_logger(__name__)


class AccountServiceError(Exception):
    """Base exception for account service errors."""
    pass


class AccountService:
    """
    Service for account management operations.
    
    Handles:
    - Querying account balance with caching
    - Querying full account information
    """
    
    def __init__(self, client: AsterDEXClient, cache_ttl: int = 5):
        """
        Initialize account service.
        
        Args:
            client: AsterDEX API client
            cache_ttl: Cache time-to-live in seconds (default 5)
        """
        self.client = client
        self._cache_ttl = cache_ttl
        self._balance_cache: Optional[List[Dict[str, Any]]] = None
        self._balance_cache_time: Optional[float] = None
    
    def _is_cache_valid(self) -> bool:
        """
        Check if balance cache is still valid.
        
        Returns:
            True if cache exists and is within TTL, False otherwise
        """
        if self._balance_cache is None or self._balance_cache_time is None:
            return False
        
        elapsed = time.time() - self._balance_cache_time
        is_valid = elapsed < self._cache_ttl
        
        logger.debug(
            "cache_validation",
            elapsed=elapsed,
            ttl=self._cache_ttl,
            is_valid=is_valid
        )
        
        return is_valid
    
    def _invalidate_cache(self) -> None:
        """Invalidate the balance cache."""
        self._balance_cache = None
        self._balance_cache_time = None
        logger.debug("cache_invalidated")
    
    async def get_balance(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get account balance information.
        
        Implements 5-second caching to reduce API calls. Cache can be
        bypassed by setting use_cache=False.
        
        Args:
            use_cache: Whether to use cached data if available (default True)
            
        Returns:
            List of balance dictionaries for each asset
            
        Raises:
            AsterDEXClientError: If API request fails
        """
        # Check cache if enabled
        if use_cache and self._is_cache_valid():
            logger.info("balance_from_cache")
            return self._balance_cache
        
        logger.info("fetching_balance_from_api", use_cache=use_cache)
        
        try:
            # Fetch balance from API
            balance = await self.client.get_account_balance()
            
            # Update cache
            self._balance_cache = balance
            self._balance_cache_time = time.time()
            
            logger.info(
                "balance_retrieved",
                assets_count=len(balance),
                cached=True
            )
            
            return balance
            
        except AsterDEXClientError as e:
            logger.error(
                "failed_to_get_balance",
                error=str(e)
            )
            raise
    
    async def get_account_info(self) -> Dict[str, Any]:
        """
        Get full account information.
        
        Returns account details including positions, balances, and
        account settings. This is not cached as it contains more
        comprehensive data.
        
        Returns:
            Account information dictionary
            
        Raises:
            AsterDEXClientError: If API request fails
        """
        logger.info("fetching_account_info")
        
        try:
            # Fetch account info from API
            account_info = await self.client.get_account_info()
            
            logger.info("account_info_retrieved")
            
            return account_info
            
        except AsterDEXClientError as e:
            logger.error(
                "failed_to_get_account_info",
                error=str(e)
            )
            raise
    
    def clear_cache(self) -> None:
        """
        Manually clear the balance cache.
        
        Useful when you know the balance has changed and want to force
        a fresh fetch on the next get_balance call.
        """
        self._invalidate_cache()
        logger.info("cache_cleared_manually")
