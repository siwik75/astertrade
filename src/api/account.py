"""Account information endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, status

from ..models.responses import BalanceResponse
from ..services.account_service import AccountService
from ..client.asterdex_client import AsterDEXClientError
from ..logging_config import get_logger
from ..security import verify_api_key


logger = get_logger(__name__)
router = APIRouter(prefix="/account", tags=["Account"])


def get_account_service() -> AccountService:
    """Dependency to get account service instance."""
    # This will be properly implemented in the main app setup
    raise NotImplementedError("Account service dependency not configured")


@router.get(
    "/balance",
    response_model=List[BalanceResponse],
    summary="Get Account Balance",
    description="Retrieve current balance information for all assets (cached for 5 seconds). Requires API key authentication.",
    responses={
        200: {
            "description": "Account balance information",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "asset": "USDT",
                            "wallet_balance": "10000.50",
                            "available_balance": "9500.25",
                            "cross_wallet_balance": "10000.50",
                            "unrealized_profit": "45.75"
                        }
                    ]
                }
            }
        }
    }
)
async def get_balance(
    account_service: AccountService = Depends(get_account_service),
    api_key: str = Depends(verify_api_key)
) -> List[BalanceResponse]:
    """
    Get account balance.
    
    Returns the current balance information for all assets in the account.
    Balance data is cached for 5 seconds to reduce API calls.
    
    Args:
        account_service: Account service dependency
        
    Returns:
        List of balance responses for each asset
        
    Raises:
        HTTPException: If API request fails
    """
    logger.info("fetching_account_balance")
    
    try:
        balances = await account_service.get_balance()
        
        logger.info(
            "balance_fetched",
            count=len(balances)
        )
        
        return [BalanceResponse(**balance) for balance in balances]
    
    except AsterDEXClientError as e:
        logger.error(
            "failed_to_fetch_balance",
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AsterDEX API error: {str(e)}"
        )
    
    except Exception as e:
        logger.error(
            "unexpected_error_fetching_balance",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/info",
    summary="Get Full Account Information",
    description="Retrieve comprehensive account details including balances, positions, and settings. Requires API key authentication.",
    responses={
        200: {
            "description": "Complete account information",
            "content": {
                "application/json": {
                    "example": {
                        "feeTier": 0,
                        "canTrade": True,
                        "canDeposit": True,
                        "canWithdraw": True,
                        "totalWalletBalance": "10000.50",
                        "totalUnrealizedProfit": "45.75",
                        "totalMarginBalance": "10046.25",
                        "availableBalance": "9500.25",
                        "assets": [
                            {
                                "asset": "USDT",
                                "walletBalance": "10000.50",
                                "unrealizedProfit": "45.75",
                                "availableBalance": "9500.25"
                            }
                        ],
                        "positions": [
                            {
                                "symbol": "BTCUSDT",
                                "positionAmt": "0.001",
                                "entryPrice": "43250.00",
                                "unrealizedProfit": "4.50",
                                "leverage": "10"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def get_account_info(
    account_service: AccountService = Depends(get_account_service),
    api_key: str = Depends(verify_api_key)
) -> dict:
    """
    Get full account information.
    
    Returns comprehensive account information including balances,
    positions, and account settings from AsterDEX.
    
    Args:
        account_service: Account service dependency
        
    Returns:
        Full account information dictionary
        
    Raises:
        HTTPException: If API request fails
    """
    logger.info("fetching_account_info")
    
    try:
        account_info = await account_service.get_account_info()
        
        logger.info("account_info_fetched")
        
        return account_info
    
    except AsterDEXClientError as e:
        logger.error(
            "failed_to_fetch_account_info",
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AsterDEX API error: {str(e)}"
        )
    
    except Exception as e:
        logger.error(
            "unexpected_error_fetching_account_info",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
