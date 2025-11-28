#!/usr/bin/env python3
"""Generate a secure API key for the AsterDEX Trading API."""

from src.security import generate_api_key

if __name__ == "__main__":
    api_key = generate_api_key()
    print("=" * 70)
    print("Generated API Key:")
    print("=" * 70)
    print(f"\n{api_key}\n")
    print("=" * 70)
    print("\nAdd this to your .env file:")
    print(f"API_KEY={api_key}")
    print("\nOr set it as an environment variable:")
    print(f"export API_KEY={api_key}")
    print("\nTo use it in requests, add this header:")
    print(f"X-API-Key: {api_key}")
    print("=" * 70)
