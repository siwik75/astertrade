#!/usr/bin/env python3
"""Test signature generation for AsterDEX"""

import json
import time
from eth_abi import encode as abi_encode
from eth_keys import keys
from eth_utils import to_bytes
from web3 import Web3

# Your credentials (replace with actual values)
USER_ADDRESS = "0xdfb0152928802a40d222c162b4808ec34832d7f3"  # Replace
SIGNER_ADDRESS = "0xd0c9d698ae0c97bcc0af24b169863a233e58e998"  # Replace
PRIVATE_KEY = "0xb6fbb3c99c04d8f489f9ac443f5c0dfd08198e096eb2c66d825ca5e09e977b52"  # Replace

def prepare_params(params):
    """Prepare parameters for signing"""
    # Remove None values
    filtered_params = {k: v for k, v in params.items() if v is not None}
    
    # Convert all values to strings
    string_params = {k: str(v) for k, v in filtered_params.items()}
    
    # Sort by keys and create JSON string
    return json.dumps(string_params, separators=(',', ':'), sort_keys=True)

def sign_request(params, user, signer, private_key):
    """Generate signature"""
    # Generate nonce
    nonce = int(time.time() * 1_000_000)
    
    # Prepare parameter string
    param_string = prepare_params(params)
    
    print(f"Param string: {param_string}")
    print(f"User: {user}")
    print(f"Signer: {signer}")
    print(f"Nonce: {nonce}")
    
    # ABI encode
    encoded = abi_encode(
        ['string', 'address', 'address', 'uint256'],
        [param_string, user, signer, nonce]
    )
    
    print(f"Encoded (hex): {encoded.hex()}")
    
    # Keccak hash
    message_hash = Web3.keccak(encoded)
    
    print(f"Message hash: {message_hash.hex()}")
    
    # Sign with eth_keys
    private_key_bytes = to_bytes(hexstr=private_key)
    eth_private_key = keys.PrivateKey(private_key_bytes)
    signature = eth_private_key.sign_msg_hash(message_hash)
    
    sig_hex = signature.to_hex()
    print(f"Signature: {sig_hex}")
    print(f"Signature length: {len(sig_hex)}")
    
    # Also try with eth_account
    from eth_account import Account
    account = Account.from_key(private_key)
    
    # Try different signing methods
    print("\n--- Alternative signing methods ---")
    
    # Method 1: sign_message with encode_defunct
    from eth_account.messages import encode_defunct
    signable = encode_defunct(primitive=message_hash)
    sig1 = account.sign_message(signable)
    print(f"Method 1 (encode_defunct): {sig1.signature.hex()}")
    
    # Method 2: unsafe_sign_hash (if available)
    try:
        sig2 = account.unsafe_sign_hash(message_hash)
        print(f"Method 2 (unsafe_sign_hash): {sig2.signature.hex()}")
    except AttributeError:
        print("Method 2 (unsafe_sign_hash): Not available")
    
    return {
        'nonce': nonce,
        'user': user,
        'signer': signer,
        'signature': sig_hex,
        'param_string': param_string,
        'message_hash': message_hash.hex()
    }

# Test with sample parameters
test_params = {
    'symbol': 'BTCUSDT',
    'timestamp': int(time.time() * 1000),
    'recvWindow': 5000
}

print("=" * 60)
print("Testing AsterDEX Signature Generation")
print("=" * 60)
print()

result = sign_request(test_params, USER_ADDRESS, SIGNER_ADDRESS, PRIVATE_KEY)

print("\n" + "=" * 60)
print("Final auth params:")
print("=" * 60)
for key, value in result.items():
    print(f"{key}: {value}")
