# API Security Guide

## Overview

Your AsterDEX Trading API now has two layers of security:

1. **Webhook Secret** - Protects webhook endpoints (TradingView signals)
2. **API Key** - Protects sensitive endpoints (positions, account, orders)

## Why API Key Authentication?

Without API key authentication, anyone who knows your server's URL can:
- View your account balance
- See your open positions
- Check your order history
- View your trading activity

With API key authentication, only requests with a valid API key can access these sensitive endpoints.

## Protected Endpoints

The following endpoints now require an API key:

### Positions
- `GET /positions` - Get all open positions
- `GET /positions/{symbol}` - Get position by symbol
- `POST /positions/{symbol}/leverage` - Update leverage
- `POST /positions/{symbol}/margin-type` - Update margin type

### Account
- `GET /account/balance` - Get account balance
- `GET /account/info` - Get full account information

### Orders
- `GET /orders` - Get order history
- `GET /orders/open` - Get open orders

## Unprotected Endpoints

These endpoints remain publicly accessible:

- `GET /health` - Health check
- `GET /docs` - API documentation
- `POST /webhook/tradingview` - TradingView webhook (protected by webhook secret)

## Setup

### 1. Generate an API Key

Run the key generation script:

```bash
python generate_api_key.py
```

This will output something like:

```
======================================================================
Generated API Key:
======================================================================

a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2

======================================================================

Add this to your .env file:
API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2

Or set it as an environment variable:
export API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2

To use it in requests, add this header:
X-API-Key: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
======================================================================
```

### 2. Add to Environment Variables

Add the API key to your `.env` file:

```bash
# API Security
API_KEY=your-generated-api-key-here
```

### 3. Restart Your Application

```bash
# Local development
docker compose restart

# On droplet
cd /opt/asterdex-trading-api
docker compose restart
```

## Usage

### Making Authenticated Requests

Include the API key in the `X-API-Key` header:

#### Using curl

```bash
curl -H "X-API-Key: your-api-key-here" \
  http://astertrade.ai/positions
```

#### Using Python requests

```python
import requests

headers = {
    "X-API-Key": "your-api-key-here"
}

response = requests.get(
    "http://astertrade.ai/positions",
    headers=headers
)

print(response.json())
```

#### Using JavaScript fetch

```javascript
fetch('http://astertrade.ai/positions', {
  headers: {
    'X-API-Key': 'your-api-key-here'
  }
})
.then(response => response.json())
.then(data => console.log(data));
```

#### In Swagger UI (/docs)

1. Visit `http://astertrade.ai/docs`
2. Click the "Authorize" button (lock icon) at the top
3. Enter your API key in the "X-API-Key" field
4. Click "Authorize"
5. Now you can test protected endpoints

## Error Responses

### Missing API Key

```bash
curl http://astertrade.ai/positions
```

Response (401 Unauthorized):
```json
{
  "detail": "API key is required. Provide it in the X-API-Key header."
}
```

### Invalid API Key

```bash
curl -H "X-API-Key: wrong-key" \
  http://astertrade.ai/positions
```

Response (403 Forbidden):
```json
{
  "detail": "Invalid API key"
}
```

### Valid API Key

```bash
curl -H "X-API-Key: correct-key" \
  http://astertrade.ai/positions
```

Response (200 OK):
```json
[
  {
    "symbol": "BTCUSDT",
    "position_amt": "0.001",
    "entry_price": "43250.50",
    ...
  }
]
```

## Security Best Practices

### 1. Keep Your API Key Secret

- ✅ Store in `.env` file (not committed to git)
- ✅ Use environment variables
- ✅ Never hardcode in source code
- ✅ Don't share in public channels
- ❌ Don't commit to git
- ❌ Don't include in logs
- ❌ Don't send over unencrypted connections

### 2. Use HTTPS in Production

Always use HTTPS when making requests with your API key:

```bash
# Good
curl -H "X-API-Key: key" https://astertrade.ai/positions

# Bad (key exposed in plain text)
curl -H "X-API-Key: key" http://astertrade.ai/positions
```

### 3. Rotate Keys Regularly

Generate a new API key periodically:

```bash
# Generate new key
python generate_api_key.py

# Update .env file
nano .env

# Restart application
docker compose restart
```

### 4. Use Different Keys for Different Environments

```bash
# Development
API_KEY=dev-key-here

# Production
API_KEY=prod-key-here
```

### 5. Monitor Access Logs

Check logs for unauthorized access attempts:

```bash
# On droplet
cd /opt/asterdex-trading-api
docker compose logs -f | grep "api_key"
```

## Webhook Security

Webhooks use a different authentication method (webhook secret):

```bash
# TradingView webhook
curl -X POST http://astertrade.ai/webhook/tradingview \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-webhook-secret" \
  -d '{"action":"buy","symbol":"BTCUSDT"}'
```

This is separate from the API key and protects webhook endpoints.

## Disabling API Key Authentication

If you want to disable API key authentication (not recommended for production):

1. Remove or comment out `API_KEY` from `.env`:
   ```bash
   # API_KEY=your-key-here
   ```

2. Restart the application:
   ```bash
   docker compose restart
   ```

3. Endpoints will return 500 error indicating API key is not configured

**Warning**: This exposes your account information to anyone who knows your URL!

## Troubleshooting

### "API key authentication is not configured on the server"

The server doesn't have an API key set. Add `API_KEY` to your `.env` file and restart.

### "API key is required"

You forgot to include the `X-API-Key` header in your request.

### "Invalid API key"

The API key you provided doesn't match the one configured on the server.

### Can't access /docs

The `/docs` endpoint is not protected and should work without an API key. If it doesn't, check if your server is running.

### Webhook not working

Webhooks use `X-Webhook-Secret`, not `X-API-Key`. Make sure you're using the correct header.

## Migration Guide

If you're upgrading from a version without API key authentication:

### 1. Generate API Key

```bash
python generate_api_key.py
```

### 2. Update .env

```bash
# Add to .env
API_KEY=your-generated-key
```

### 3. Update Clients

Update any scripts or applications that call your API:

```python
# Before
response = requests.get("http://astertrade.ai/positions")

# After
headers = {"X-API-Key": "your-api-key"}
response = requests.get("http://astertrade.ai/positions", headers=headers)
```

### 4. Deploy

```bash
# Local
docker compose restart

# Droplet
ssh root@YOUR_IP
cd /opt/asterdex-trading-api
git pull
docker compose restart
```

## Example: Complete Setup

```bash
# 1. Generate API key
python generate_api_key.py

# 2. Add to .env
echo "API_KEY=a1b2c3d4e5f6..." >> .env

# 3. Restart
docker compose restart

# 4. Test
curl -H "X-API-Key: a1b2c3d4e5f6..." \
  http://localhost:8000/positions

# 5. Deploy to droplet
git add .env.example  # Don't commit actual .env!
git commit -m "Add API key authentication"
git push

# 6. On droplet
ssh root@YOUR_IP
cd /opt/asterdex-trading-api
git pull
nano .env  # Add API_KEY
docker compose restart
```

## Summary

- **Protected**: `/positions`, `/account`, `/orders` - Require `X-API-Key` header
- **Public**: `/health`, `/docs` - No authentication needed
- **Webhook**: `/webhook/*` - Require `X-Webhook-Secret` header
- **Generate Key**: `python generate_api_key.py`
- **Use Key**: Add `X-API-Key: your-key` header to requests
- **Store Key**: In `.env` file as `API_KEY=your-key`

Your sensitive account information is now protected! 🔒
