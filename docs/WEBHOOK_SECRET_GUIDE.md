# Webhook Secret Security Guide

## What is WEBHOOK_SECRET?

`WEBHOOK_SECRET` is a security token that validates incoming webhook requests from TradingView. It ensures that only authorized requests can trigger trades on your account.

## Why You Need It

**Without `WEBHOOK_SECRET`:**
- ❌ Anyone who discovers your webhook URL can send fake trading signals
- ❌ Malicious actors could open/close positions without authorization
- ❌ No way to verify the request is actually from TradingView
- ❌ Your trading bot is vulnerable to unauthorized access

**With `WEBHOOK_SECRET`:**
- ✅ Only requests with the correct secret are accepted
- ✅ Unauthorized requests are rejected with 401 error
- ✅ Adds an authentication layer to your webhook
- ✅ Protects your trading account from unauthorized trades

## How It Works

### 1. You Set the Secret

In your `.env` file or DigitalOcean environment variables:
```bash
WEBHOOK_SECRET=your-super-secret-random-string-here
```

### 2. TradingView Sends the Secret

When TradingView sends a webhook, it includes the secret in the HTTP header:
```
POST /webhook/tradingview
Headers:
  Content-Type: application/json
  X-Webhook-Secret: your-super-secret-random-string-here
Body:
  {"action": "open", "symbol": "BTCUSDT", ...}
```

### 3. Your API Validates

Your API checks if the secret matches:
```python
# From src/api/webhook.py
if settings.is_webhook_secret_configured():
    if not x_webhook_secret:
        # No secret provided - reject
        raise HTTPException(status_code=401, detail="Webhook secret required")
    
    if x_webhook_secret != settings.webhook_secret:
        # Wrong secret - reject
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

# Secret matches - process the trade
```

## Setting Up WEBHOOK_SECRET

### Step 1: Generate a Strong Secret

**Option 1: Use OpenSSL (Recommended)**
```bash
openssl rand -hex 32
# Output: a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

**Option 2: Use Python**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Output: xK7mP9nQ2rS5tU8vW1xY4zA6bC9dE2fG3hI6jK9lM2nO5pQ8rS1tU4vW7xY0zA3b
```

**Option 3: Use Online Generator**
- Visit: https://www.random.org/strings/
- Generate a random string (32+ characters)

**Requirements:**
- ✅ At least 32 characters long
- ✅ Mix of letters, numbers, and special characters
- ✅ Completely random (don't use words or patterns)
- ✅ Unique to your deployment

### Step 2: Add to Your Environment

**For Local Development (.env file):**
```bash
# .env
WEBHOOK_SECRET=a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

**For DigitalOcean App Platform:**
1. Go to your App settings
2. Navigate to "Environment Variables"
3. Add new variable:
   - Key: `WEBHOOK_SECRET`
   - Value: `your-generated-secret`
   - **Important:** Mark as "Encrypted" ✅
4. Save and redeploy

**For DigitalOcean Droplet:**
```bash
# SSH into your Droplet
ssh root@YOUR_DROPLET_IP

# Edit .env file
cd /opt/asterdex-trading-api
nano .env

# Add the line:
WEBHOOK_SECRET=your-generated-secret

# Save (Ctrl+X, Y, Enter)

# Restart the service
docker compose restart
```

### Step 3: Configure TradingView

**The Challenge:**
TradingView's webhook UI doesn't support custom HTTP headers directly. Here are your options:

#### Option A: Use a Webhook Proxy (Recommended for Production)

Create a simple proxy that adds the header. Here's a Cloudflare Worker example:

```javascript
// Cloudflare Worker
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  // Only allow POST requests
  if (request.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 })
  }
  
  // Get the request body
  const body = await request.text()
  
  // Forward to your API with the secret header
  const response = await fetch('https://your-app.ondigitalocean.app/webhook/tradingview', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Secret': 'your-generated-secret'  // Add your secret here
    },
    body: body
  })
  
  return response
}
```

**Setup:**
1. Create a Cloudflare Worker (free tier available)
2. Deploy the code above with your secret
3. Use the Worker URL in TradingView: `https://your-worker.workers.dev`

#### Option B: Use Query Parameter (Less Secure)

Modify your webhook endpoint to accept the secret as a query parameter:

**In TradingView:**
```
https://your-app.ondigitalocean.app/webhook/tradingview?secret=your-generated-secret
```

**Note:** This is less secure because:
- The secret appears in URL logs
- URLs can be cached by proxies
- Not recommended for production

To implement this, you'd need to modify `src/api/webhook.py` to check query parameters.

#### Option C: Disable for Testing (Not Recommended for Production)

For local testing only, you can leave `WEBHOOK_SECRET` unset:

```bash
# .env - comment out or remove
# WEBHOOK_SECRET=
```

**Warning:** Only use this for local testing! Always enable in production.

## Testing Your Setup

### Test 1: Without Secret (Should Fail)

```bash
curl -X POST https://your-app.ondigitalocean.app/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{
    "action": "open",
    "symbol": "BTCUSDT",
    "side": "BUY",
    "quantity": "0.001",
    "order_type": "MARKET"
  }'

# Expected Response:
# {"detail": "Webhook secret required but not provided"}
# Status: 401 Unauthorized
```

### Test 2: With Wrong Secret (Should Fail)

```bash
curl -X POST https://your-app.ondigitalocean.app/webhook/tradingview \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: wrong-secret" \
  -d '{
    "action": "open",
    "symbol": "BTCUSDT",
    "side": "BUY",
    "quantity": "0.001",
    "order_type": "MARKET"
  }'

# Expected Response:
# {"detail": "Invalid webhook secret"}
# Status: 401 Unauthorized
```

### Test 3: With Correct Secret (Should Succeed)

```bash
curl -X POST https://your-app.ondigitalocean.app/webhook/tradingview \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-generated-secret" \
  -d '{
    "action": "open",
    "symbol": "BTCUSDT",
    "side": "BUY",
    "quantity": "0.001",
    "order_type": "MARKET"
  }'

# Expected Response:
# {"success": true, "message": "Position opened successfully for BTCUSDT", ...}
# Status: 200 OK
```

## Security Best Practices

### 1. Keep Your Secret... Secret!

**DO:**
- ✅ Store in environment variables
- ✅ Mark as "Encrypted" in DigitalOcean
- ✅ Use different secrets for dev/staging/production
- ✅ Rotate periodically (every 3-6 months)

**DON'T:**
- ❌ Commit to Git
- ❌ Share in public forums
- ❌ Include in error messages or logs
- ❌ Send over unencrypted channels

### 2. Use Strong Secrets

**Good:**
```
a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
xK7mP9nQ2rS5tU8vW1xY4zA6bC9dE2fG3hI6jK9lM2nO5pQ8rS1tU4vW7xY0zA3b
```

**Bad:**
```
password123
my-secret
tradingview-webhook
btc-trading-bot
```

### 3. Rotate Regularly

Change your secret every 3-6 months:

```bash
# Generate new secret
openssl rand -hex 32

# Update in DigitalOcean
# Update in your proxy/TradingView setup

# Monitor logs to ensure old secret stops being used
```

### 4. Monitor for Unauthorized Attempts

Check your logs regularly for failed authentication:

```bash
# View logs
docker compose logs -f | grep "webhook_invalid_secret"

# Or in DigitalOcean App Platform
# Go to Runtime Logs and search for "webhook_invalid_secret"
```

If you see many failed attempts:
- ✅ Rotate your secret immediately
- ✅ Check if your webhook URL was leaked
- ✅ Consider adding rate limiting
- ✅ Review access logs for suspicious IPs

## Troubleshooting

### Issue: "Webhook secret required but not provided"

**Cause:** Your API expects a secret, but the request doesn't include it.

**Solutions:**
1. Add `X-Webhook-Secret` header to your requests
2. Use a webhook proxy to add the header
3. Temporarily disable secret for testing (not recommended)

### Issue: "Invalid webhook secret"

**Cause:** The secret in the request doesn't match your configured secret.

**Solutions:**
1. Verify the secret in your `.env` or DigitalOcean settings
2. Check for typos or extra spaces
3. Ensure you're using the correct secret (dev vs production)
4. Regenerate and update both sides

### Issue: TradingView webhooks not working

**Cause:** TradingView can't send custom headers.

**Solutions:**
1. Use a webhook proxy (Cloudflare Workers, AWS API Gateway)
2. Modify your API to accept secret in query parameter (less secure)
3. For testing only: disable webhook secret

### Issue: Secret visible in logs

**Cause:** Logging the full request headers or URL.

**Solution:** The API already masks secrets in logs. Verify by checking:
```bash
docker compose logs | grep "WEBHOOK_SECRET"
# Should show: ***REDACTED***
```

## Advanced: Implementing Query Parameter Support

If you want to accept the secret as a query parameter (for easier TradingView integration), modify `src/api/webhook.py`:

```python
from fastapi import Query

@router.post("/tradingview")
async def tradingview_webhook(
    request: WebhookRequest,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    secret: Optional[str] = Query(None),  # Add query parameter support
    trading_service: TradingService = Depends(get_trading_service)
) -> WebhookResponse:
    settings = get_settings()
    
    # Check both header and query parameter
    provided_secret = x_webhook_secret or secret
    
    if settings.is_webhook_secret_configured():
        if not provided_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Webhook secret required but not provided"
            )
        
        if provided_secret != settings.webhook_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook secret"
            )
    
    # Rest of the code...
```

Then in TradingView:
```
https://your-app.ondigitalocean.app/webhook/tradingview?secret=your-secret
```

**Warning:** This is less secure but more convenient for TradingView.

## Recommended Setup

For production, I recommend:

1. **Generate a strong secret** (32+ characters)
2. **Store in DigitalOcean** (marked as encrypted)
3. **Use Cloudflare Worker** as a proxy to add the header
4. **Monitor logs** for unauthorized attempts
5. **Rotate every 3-6 months**

This provides the best balance of security and usability.

## Summary

- `WEBHOOK_SECRET` protects your trading bot from unauthorized access
- Set it to a strong, random 32+ character string
- Store securely in environment variables (encrypted)
- TradingView doesn't support custom headers, so use a proxy
- Test thoroughly before going live
- Monitor logs for unauthorized attempts
- Rotate periodically for best security

**Bottom line:** Always use `WEBHOOK_SECRET` in production. It's your first line of defense against unauthorized trading signals.
