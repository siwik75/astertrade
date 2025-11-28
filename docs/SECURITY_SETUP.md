# Quick Security Setup

## 🔒 Secure Your API in 3 Steps

### Step 1: Generate API Key

```bash
python generate_api_key.py
```

Copy the generated key.

### Step 2: Add to .env

```bash
nano .env
```

Add this line:
```
API_KEY=paste-your-generated-key-here
```

Save and exit (Ctrl+X, Y, Enter).

### Step 3: Restart

```bash
docker compose restart
```

Done! Your sensitive endpoints are now protected.

## Test It

### Without API Key (Should Fail)

```bash
curl http://localhost:8000/positions
```

Expected response:
```json
{
  "detail": "API key is required. Provide it in the X-API-Key header."
}
```

### With API Key (Should Work)

```bash
curl -H "X-API-Key: your-key-here" \
  http://localhost:8000/positions
```

Expected response:
```json
[
  {
    "symbol": "BTCUSDT",
    "position_amt": "0.001",
    ...
  }
]
```

## Deploy to Droplet

```bash
# 1. SSH into droplet
ssh root@YOUR_DROPLET_IP

# 2. Navigate to app
cd /opt/asterdex-trading-api

# 3. Generate key
python generate_api_key.py

# 4. Add to .env
nano .env
# Add: API_KEY=your-generated-key

# 5. Restart
docker compose restart

# 6. Test
curl -H "X-API-Key: your-key" \
  http://localhost:8000/positions
```

## What's Protected?

✅ Protected (requires API key):
- `/positions` - Your open positions
- `/account/balance` - Your account balance
- `/account/info` - Your account details
- `/orders` - Your order history

✅ Public (no API key needed):
- `/` - Welcome page
- `/health` - Health check
- `/docs` - API documentation

✅ Webhook (requires webhook secret):
- `/webhook/tradingview` - TradingView signals

## Need Help?

See [API_SECURITY.md](API_SECURITY.md) for complete documentation.
