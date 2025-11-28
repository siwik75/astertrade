#!/usr/bin/env python3
"""Test script to check if OpenAPI spec includes security scheme."""

import json
import sys
import os

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Import the app
from src.app import app

# Get OpenAPI schema
openapi_schema = app.openapi()

# Check for security schemes
print("=" * 70)
print("OpenAPI Security Check")
print("=" * 70)
print()

# Check if securitySchemes exists
if "components" in openapi_schema and "securitySchemes" in openapi_schema["components"]:
    print("✅ Security schemes found:")
    print(json.dumps(openapi_schema["components"]["securitySchemes"], indent=2))
else:
    print("❌ No security schemes found in OpenAPI spec")
    print()
    print("Components:", list(openapi_schema.get("components", {}).keys()))

print()
print("=" * 70)
print("Checking Protected Endpoints")
print("=" * 70)
print()

# Check a few endpoints for security requirements
endpoints_to_check = [
    ("/positions", "get"),
    ("/account/balance", "get"),
    ("/orders", "get"),
    ("/health", "get"),
]

for path, method in endpoints_to_check:
    if path in openapi_schema["paths"] and method in openapi_schema["paths"][path]:
        endpoint = openapi_schema["paths"][path][method]
        has_security = "security" in endpoint
        
        if has_security:
            print(f"✅ {method.upper():6} {path:20} - Security: {endpoint['security']}")
        else:
            print(f"⚠️  {method.upper():6} {path:20} - No security")
    else:
        print(f"❌ {method.upper():6} {path:20} - Not found")

print()
print("=" * 70)
