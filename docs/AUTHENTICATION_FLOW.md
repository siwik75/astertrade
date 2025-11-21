# Authentication Flow Explained

## The Confusion

You're absolutely right to question this! There are **TWO separate authentication layers**, and it's important to understand the difference.

## The Two Authentication Layers

```
┌─────────────┐                    ┌─────────────┐                    ┌─────────────┐
│             │  webhook_secret    │             │  user/signer/sig   │             │
│ TradingView │ ─────────────────> │  Your API   │ ─────────────────> │  AsterDEX   │
│             │                    │             │                    │             │
└─────────────┘                    └─────────────┘                    └─────────────┘
     Layer 1                            Layer 2
```

### Layer 1: TradingView → Your API

**Purpose:** Verify the webhook is from TradingView (or authorized source)

**Authentication Method:** `webhook_secret`

**What TradingView sends:**
```json
{
  "action": "open",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "quantity": "0.001",
  "webhook_secret": "your-secret-here"
}
```

**What YOUR API checks:**
- Does `webhook_secret` match the configured secret?
- If yes → Process the request
- If no → Reject with 401

**You configure this in:**
- `.env` file: `WEBHOOK_SECRET=your-secret`
- TradingView alert message: Include `webhook_secret` field

---

### Layer 2: Your API → AsterDEX

**Purpose:** Authenticate YOUR API with AsterDEX to execute trades

**Authentication Method:** `user`, `signer`, `nonce`, `signature`

**What YOUR API sends to AsterDEX:**
```json
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "quantity": "0.001",
  "type": "MARKET",
  "timestamp": 1700000000000,
  "recvWindow": 5000,
  "user": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "signer": "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199",
  "nonce": 1700000000000000,
  "signature": "0xabcdef1234567890..."
}
```

**What AsterDEX checks:**
- Is `signer` authorized for `user`?
- Does `signature` match the request parameters?
- Is `nonce` valid (not replayed)?
- If yes → Execute trade
- If no → Reject

**You configure this in:**
- `.env` file: `ASTERDEX_USER_ADDRESS`, `ASTERDEX_SIGNER_ADDRESS`, `ASTERDEX_PRIVATE_KEY`
- YOUR API handles this automatically!

---

## The Key Point: Your API Handles Layer 2 Automatically

**You (TradingView user) only need to worry about Layer 1.**

Your API automatically adds the AsterDEX authentication (Layer 2) for you!

### Code Flow

**1. TradingView sends webhook:**
```json
{
  "action": "open",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "quantity": "0.001",
  "webhook_secret": "your-secret"
}
```

**2. Your API receives it (src/api/webhook.py):**
```python
async def tradingview_webhook(request: WebhookRequest, ...):
    # Check webhook_secret (Layer 1)
    if request.webhook_secret != settings.webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    
    # Process the trade
    result = await trading_service.open_position(
        symbol=request.symbol,
        side=request.side,
        quantity=request.quantity
    )
```

**3. Trading service calls AsterDEX client:**
```python
# src/services/trading_service.py
async def open_position(self, symbol, side, quantity):
    order_params = {
        "symbol": symbol,
        "side": side,
        "quantity": str(quantity),
        "type": "MARKET"
    }
    
    # Call AsterDEX API
    result = await self.client.create_order(order_params)
    return result
```

**4. AsterDEX client adds authentication (Layer 2):**
```python
# src/client/asterdex_client.py
async def create_order(self, order_params):
    # Add timestamp and recvWindow
    params = self._add_timestamp_and_recv_window(order_params)
    
    # Add authentication (user, signer, nonce, signature)
    params = self.auth.add_auth_params(params)
    
    # Now params includes:
    # {
    #   "symbol": "BTCUSDT",
    #   "side": "BUY",
    #   "quantity": "0.001",
    #   "type": "MARKET",
    #   "timestamp": 1700000000000,
    #   "recvWindow": 5000,
    #   "user": "0x742d35...",
    #   "signer": "0x8626f6...",
    #   "nonce": 1700000000000000,
    #   "signature": "0xabcdef..."
    # }
    
    # Send to AsterDEX
    response = await self.client.post(url, params=params)
    return response
```

**5. Authenticator creates signature:**
```python
# src/client/authenticator.py
def add_auth_params(self, params):
    # Generate nonce
    nonce = self.generate_nonce()
    
    # Create signature
    signature = self.sign_request(params, nonce)
    
    # Add auth fields
    params['user'] = self.user
    params['signer'] = self.signer
    params['nonce'] = nonce
    params['signature'] = signature
    
    return params
```

---

## Visual Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ TradingView Alert                                               │
│                                                                 │
│ Webhook Message:                                                │
│ {                                                               │
│   "action": "open",                                             │
│   "symbol": "BTCUSDT",                                          │
│   "side": "BUY",                                                │
│   "quantity": "0.001",                                          │
│   "webhook_secret": "your-secret"  ← Layer 1 Auth              │
│ }                                                               │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS POST
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Your API (DigitalOcean)                                         │
│                                                                 │
│ 1. Verify webhook_secret ✓                                     │
│ 2. Parse trading action                                         │
│ 3. Call trading_service.open_position()                         │
│ 4. Trading service calls asterdex_client.create_order()         │
│ 5. Client adds authentication automatically:                    │
│    - user: 0x742d35...                                          │
│    - signer: 0x8626f6...                                        │
│    - nonce: 1700000000000000                                    │
│    - signature: 0xabcdef... (signed with private key)           │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS POST
                         │ {
                         │   "symbol": "BTCUSDT",
                         │   "side": "BUY",
                         │   "quantity": "0.001",
                         │   "type": "MARKET",
                         │   "timestamp": 1700000000000,
                         │   "user": "0x742d35...",
                         │   "signer": "0x8626f6...",
                         │   "nonce": 1700000000000000,
                         │   "signature": "0xabcdef..."  ← Layer 2 Auth
                         │ }
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ AsterDEX API                                                    │
│                                                                 │
│ 1. Verify signature ✓                                          │
│ 2. Check signer authorized for user ✓                          │
│ 3. Validate nonce ✓                                            │
│ 4. Execute trade on user's account                             │
│ 5. Return result                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## What You Need to Configure

### For Layer 1 (TradingView → Your API)

**In your .env file:**
```bash
WEBHOOK_SECRET=your-random-secret-here
```

**In TradingView alert message:**
```json
{
  "action": "open",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "quantity": "0.001",
  "webhook_secret": "your-random-secret-here"
}
```

### For Layer 2 (Your API → AsterDEX)

**In your .env file:**
```bash
ASTERDEX_USER_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
ASTERDEX_SIGNER_ADDRESS=0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199
ASTERDEX_PRIVATE_KEY=0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
```

**In TradingView alert message:**
```
Nothing! Your API handles this automatically.
```

---

## Why This Design?

### Security Benefits

1. **Separation of Concerns**
   - TradingView doesn't need to know your AsterDEX credentials
   - Your API acts as a secure gateway
   - Only your API has access to private keys

2. **Simplified TradingView Setup**
   - TradingView only needs to know `webhook_secret`
   - No complex signature generation in TradingView
   - Easy to set up and maintain

3. **Centralized Authentication**
   - All AsterDEX authentication in one place (your API)
   - Easy to update credentials
   - Better security monitoring

4. **Flexibility**
   - Can add additional validation in your API
   - Can implement rate limiting
   - Can add custom business logic

### Real-World Analogy

```
TradingView = Customer at restaurant
Your API = Waiter
AsterDEX = Kitchen

Customer tells waiter: "I want a burger" + shows membership card
Waiter verifies membership card (webhook_secret)
Waiter tells kitchen: "Table 5 wants a burger" + shows employee badge
Kitchen verifies employee badge (user/signer/signature)
Kitchen prepares burger

Customer doesn't need kitchen credentials!
Waiter handles authentication with kitchen.
```

---

## Testing Both Layers

### Test Layer 1 (Webhook Secret)

```bash
# Without secret - should FAIL
curl -X POST https://your-app/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{
    "action": "close",
    "symbol": "BTCUSDT"
  }'

# Response: 401 Unauthorized - "Webhook secret required"

# With secret - should SUCCEED
curl -X POST https://your-app/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{
    "action": "close",
    "symbol": "BTCUSDT",
    "webhook_secret": "your-secret"
  }'

# Response: 200 OK - Trade executed
```

### Test Layer 2 (AsterDEX Authentication)

This is tested automatically when your API starts:

```bash
docker compose up -d
docker compose logs | grep "authenticator_initialized"

# Should see:
# authenticator_initialized user=0x742d35... signer=0x8626f6...

# If you see error:
# "Private key does not match signer address"
# → Fix your ASTERDEX_SIGNER_ADDRESS or ASTERDEX_PRIVATE_KEY
```

Then test actual API call:

```bash
# This tests Layer 2 authentication
curl http://localhost:8000/account/balance

# If you see balance data → Layer 2 works! ✓
# If you see 401/403 → Check AsterDEX credentials
```

---

## Common Confusion Points

### Q: "Do I need to add user/signer/signature to TradingView webhook?"

**A: No!** TradingView only needs:
- Trading parameters (action, symbol, side, quantity)
- `webhook_secret` (for Layer 1 authentication)

Your API adds user/signer/signature automatically when talking to AsterDEX.

### Q: "Where does the signature come from?"

**A:** Your API generates it automatically using:
- Request parameters
- `ASTERDEX_USER_ADDRESS`
- `ASTERDEX_SIGNER_ADDRESS`
- `ASTERDEX_PRIVATE_KEY`
- Current timestamp (nonce)

See `src/client/authenticator.py` for the implementation.

### Q: "Can I call AsterDEX directly from TradingView?"

**A:** Technically yes, but:
- ❌ You'd need to generate signatures in TradingView (complex)
- ❌ You'd expose your private key to TradingView
- ❌ No centralized control or monitoring
- ✅ Better to use your API as a secure gateway

### Q: "What if webhook_secret is wrong but AsterDEX credentials are correct?"

**A:** Request fails at Layer 1 (your API rejects it). Never reaches AsterDEX.

### Q: "What if webhook_secret is correct but AsterDEX credentials are wrong?"

**A:** Request passes Layer 1, fails at Layer 2 (AsterDEX rejects it).

---

## Summary

### Two Separate Authentication Layers

| Layer | From → To | Method | You Configure |
|-------|-----------|--------|---------------|
| **Layer 1** | TradingView → Your API | `webhook_secret` | In TradingView alert message |
| **Layer 2** | Your API → AsterDEX | `user/signer/signature` | In .env file (automatic) |

### What You Need to Do

**In .env file:**
```bash
# Layer 1
WEBHOOK_SECRET=your-random-secret

# Layer 2 (handled automatically by your API)
ASTERDEX_USER_ADDRESS=0x742d35...
ASTERDEX_SIGNER_ADDRESS=0x8626f6...
ASTERDEX_PRIVATE_KEY=0xabcdef...
```

**In TradingView alert:**
```json
{
  "action": "open",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "quantity": "0.001",
  "webhook_secret": "your-random-secret"
}
```

**That's it!** Your API handles the rest automatically.

### Key Takeaway

**You only configure Layer 1 in TradingView.**

**Your API automatically handles Layer 2 (AsterDEX authentication) for you.**

This is by design - it keeps your AsterDEX credentials secure and makes TradingView setup simple!
