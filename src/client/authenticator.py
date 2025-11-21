"""AsterDEX authentication handler for API request signing"""

import json
import time
from typing import Dict, Any
from eth_abi import encode as abi_encode
from eth_account import Account
from web3 import Web3

from ..logging_config import get_logger


logger = get_logger(__name__)


class AsterDEXAuthenticator:
    """
    Handles authentication for AsterDEX API requests.
    
    Implements the AsterDEX authentication protocol:
    1. Generate nonce from current timestamp
    2. Prepare parameters (convert to strings, sort by ASCII)
    3. ABI encode with user, signer, and nonce
    4. Keccak hash the encoded data
    5. ECDSA sign with private key
    """
    
    def __init__(self, user: str, signer: str, private_key: str):
        """
        Initialize authenticator with wallet addresses and private key.
        
        Args:
            user: Main wallet address registered on AsterDEX
            signer: API wallet address used for signing
            private_key: Private key for the signer wallet
        """
        self.user = user.lower() if user.startswith("0x") else f"0x{user}".lower()
        self.signer = signer.lower() if signer.startswith("0x") else f"0x{signer}".lower()
        
        # Ensure private key has 0x prefix
        if not private_key.startswith("0x"):
            private_key = f"0x{private_key}"
        
        self.private_key = private_key
        self.account = Account.from_key(private_key)
        
        # Verify signer address matches private key
        if self.account.address.lower() != self.signer:
            logger.error(
                "signer_address_mismatch",
                expected=self.signer,
                actual=self.account.address.lower()
            )
            raise ValueError(
                f"Private key does not match signer address. "
                f"Expected: {self.signer}, Got: {self.account.address.lower()}"
            )
        
        logger.info(
            "authenticator_initialized",
            user=self.user,
            signer=self.signer
        )
    
    def generate_nonce(self) -> int:
        """
        Generate nonce using current timestamp in microseconds.
        
        Returns:
            Nonce as integer (microseconds since epoch)
        """
        return int(time.time() * 1_000_000)
    
    def prepare_params(self, params: Dict[str, Any]) -> str:
        """
        Prepare parameters for signing by converting to sorted JSON string.
        
        Process:
        1. Remove None values
        2. Convert all values to strings
        3. Sort keys by ASCII order
        4. Return JSON string without spaces
        
        Args:
            params: Dictionary of request parameters
            
        Returns:
            JSON string with sorted keys and string values
        """
        # Remove None values
        filtered_params = {k: v for k, v in params.items() if v is not None}
        
        # Convert all values to strings
        string_params = {k: str(v) for k, v in filtered_params.items()}
        
        # Sort by keys in ASCII order and create JSON string without spaces
        sorted_keys = sorted(string_params.keys())
        sorted_params = {k: string_params[k] for k in sorted_keys}
        
        # Return JSON without spaces (separators with no space after comma/colon)
        return json.dumps(sorted_params, separators=(',', ':'), sort_keys=True)
    
    def sign_request(self, params: Dict[str, Any], nonce: int) -> str:
        """
        Generate signature for API request.
        
        Process:
        1. Prepare parameter string
        2. ABI encode with types: string, address, address, uint256
        3. Keccak hash the encoded data
        4. ECDSA sign with private key
        5. Return hex signature
        
        Args:
            params: Request parameters to sign
            nonce: Nonce value (microsecond timestamp)
            
        Returns:
            Hex signature string with 0x prefix
        """
        # Prepare parameter string
        param_string = self.prepare_params(params)
        
        # ABI encode with string, address, address, uint256 types
        encoded = abi_encode(
            ['string', 'address', 'address', 'uint256'],
            [param_string, self.user, self.signer, nonce]
        )
        
        # Keccak hash the encoded data
        message_hash = Web3.keccak(encoded)
        
        # ECDSA sign with private key
        signed_message = self.account.signHash(message_hash)
        
        # Return hex signature
        return signed_message.signature.hex()
    
    def add_auth_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add authentication parameters to request.
        
        Adds: nonce, user, signer, signature
        
        Args:
            params: Original request parameters
            
        Returns:
            Parameters with authentication fields added
        """
        # Create a copy to avoid modifying original
        auth_params = params.copy()
        
        # Generate nonce
        nonce = self.generate_nonce()
        
        # Generate signature for the original params (without auth fields)
        signature = self.sign_request(params, nonce)
        
        # Add authentication parameters
        auth_params['nonce'] = nonce
        auth_params['user'] = self.user
        auth_params['signer'] = self.signer
        auth_params['signature'] = signature
        
        return auth_params
