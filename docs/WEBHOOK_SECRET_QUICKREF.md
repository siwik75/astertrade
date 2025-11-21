# WEBHOOK_SECRET Quick Reference

## What It Does
Validates that webhook requests are authorized before executing trades.

## Setup (2 Steps - Easy Method)

### 1. Generate Secret
```bash
openssl rand -hex 32
```

### 2. Add to Environment
```bash
# .env file
WEBHOOK_SECRET=your-generated-secret-here
```

### 3. Use in TradingView (Choose One)

**Method A: In JSON Body (Recommended - No Proxy Needed!)**
```json
{
  "action": "open",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "quantity": "0.001",
  "webhook_secret": "your-generated-secret-here"
}
```

Webhook URL: `https://your-app.ondigitalocean.app/webhook/tradingview`

**Method B: In HTTP Header (More Secure - Requires Proxy)**

Use a webhook proxy (Cloudflare Worker) to add the header:
```javascript
// Cloudflare Worker
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const body = await request.text()
  
  return fetch('https://your-app.ondigitalocean.app/webhook/tradingview', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Secret': 'your-generated-secret-here'
    },
    body: body
  })
}
```

Webhook URL: `https://your-worker.workers.dev`

## Testing

```bash
# Should FAIL (no secret)
curl -X POST https://your-app/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{"action":"close","symbol":"BTCUSDT"}'

# Should SUCCEED (secret in body - recommended)
curl -X POST https://your-app/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{"action":"close","symbol":"BTCUSDT","webhook_secret":"your-secret"}'

# Should SUCCEED (secret in header - also works)
curl -X POST https://your-app/webhook/tradingview \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secret" \
  -d '{"action":"close","symbol":"BTCUSDT"}'
```

## Security Checklist

- [ ] Secret is 32+ characters
- [ ] Secret is random (not a word or pattern)
- [ ] Stored in environment variables
- [ ] Marked as "Encrypted" in DigitalOcean
- [ ] Not committed to Git
- [ ] Different for dev/staging/production
- [ ] Rotated every 3-6 months

## Common Issues

| Issue | Solution |
|-------|----------|
| "Webhook secret required" | Add `webhook_secret` to JSON body OR `X-Webhook-Secret` header |
| "Invalid webhook secret" | Check for typos, verify secret matches |
| TradingView can't send headers | Use `webhook_secret` in JSON body instead! |
| Secret in logs | Already masked by API automatically |

## Quick Commands

```bash
# Generate secret
openssl rand -hex 32

# Test without secret (should fail)
curl -X POST https://your-app/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{"action":"close","symbol":"BTCUSDT"}'

# Test with secret in body (recommended - should work)
curl -X POST https://your-app/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{"action":"close","symbol":"BTCUSDT","webhook_secret":"YOUR_SECRET"}'

# Test with secret in header (also works)
curl -X POST https://your-app/webhook/tradingview \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: YOUR_SECRET" \
  -d '{"action":"close","symbol":"BTCUSDT"}'

# Check logs for failed attempts
docker compose logs | grep "webhook_invalid_secret"
```

## Recommended: Use Body Method (No Proxy Needed!)

**TradingView Alert Message:**
```json
{
  "action": "open",
  "symbol": "{{ticker}}",
  "side": "BUY",
  "quantity": "0.001",
  "webhook_secret": "your-generated-secret-here"
}
```

**Webhook URL:**
```
https://your-app.ondigitalocean.app/webhook/tradingview
```

**That's it!** No proxy, no Cloudflare Worker needed.

## Alternative: Cloudflare Worker (More Secure)

Only needed if you want secret in header instead of body:

1. Go to https://workers.cloudflare.com
2. Create new Worker
3. Paste the code from Method B above
4. Replace `your-app.ondigitalocean.app` with your URL
5. Replace `your-generated-secret-here` with your secret
6. Deploy
7. Use Worker URL in TradingView

**Cost:** Free (100,000 requests/day)

## For Full Details

See: `docs/WEBHOOK_SECRET_GUIDE.md`
