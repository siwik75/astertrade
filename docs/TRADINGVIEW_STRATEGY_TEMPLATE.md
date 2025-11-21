# TradingView Strategy to AsterDEX Bot Template

## Your Current Strategy Analysis

Based on your notifications, your strategy:
- Uses `{{strategy.order.action}}` (buy/sell)
- Uses `{{strategy.order.contracts}}` for quantity
- Tracks `{{strategy.position_size}}` for current position

## The Challenge

Your strategy generates orders like:
- "buy @ 0.575181" when position is 0 → **Open Long**
- "sell @ 0.152568" when position is 0.575181 → **Close Long + Open Short**
- "sell @ 0.166842" when position is -0.575181 → **Reduce Short**
- "buy @ 0.30691" when position is -0.30691 → **Close Short**

We need to translate these into our API's actions: `open`, `increase`, `decrease`, `close`

## Solution: Smart Webhook Template

Unfortunately, TradingView's webhook message format doesn't support conditional logic directly. You have **two options**:

### Option 1: Simple Template (Recommended for Most Cases)

This template works for basic strategies where you want to mirror the strategy's position:

```json
{
  "action": "{{strategy.order.action}}",
  "symbol": "BTCUSDT",
  "side": "{{strategy.order.action}}",
  "quantity": "{{strategy.order.contracts}}",
  "order_type": "MARKET",
  "position_size": "{{strategy.position_size}}"
}
```

**Problem:** This won't work directly because our API expects specific actions (open/close/increase/decrease), not buy/sell.

### Option 2: Modified API to Handle Strategy Orders (BEST SOLUTION)

Let me create a new endpoint specifically for TradingView strategy webhooks that understands the strategy context.

## Recommended Webhook Message Template

Use this template in your TradingView alert:

```json
{
  "strategy_action": "{{strategy.order.action}}",
  "symbol": "BTCUSDT",
  "quantity": "{{strategy.order.contracts}}",
  "position_before": "{{strategy.prev_position_size}}",
  "position_after": "{{strategy.position_size}}",
  "order_type": "MARKET"
}
```

**Note:** We need to add a new endpoint `/webhook/tradingview-strategy` that can interpret these strategy-specific variables.

## Alternative: Multiple Alerts Approach

If you want to use the existing endpoint without modifications, create separate alerts for each scenario:

### Alert 1: Open Long Position
**Condition:** Strategy enters long (position goes from 0 to positive)
**Message:**
```json
{
  "action": "open",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "quantity": "{{strategy.order.contracts}}",
  "order_type": "MARKET"
}
```

### Alert 2: Open Short Position
**Condition:** Strategy enters short (position goes from 0 to negative)
**Message:**
```json
{
  "action": "open",
  "symbol": "BTCUSDT",
  "side": "SELL",
  "quantity": "{{strategy.order.contracts}}",
  "order_type": "MARKET"
}
```

### Alert 3: Close Position
**Condition:** Strategy exits (position goes to 0)
**Message:**
```json
{
  "action": "close",
  "symbol": "BTCUSDT"
}
```

### Alert 4: Increase Position
**Condition:** Strategy adds to position (same direction)
**Message:**
```json
{
  "action": "increase",
  "symbol": "BTCUSDT",
  "quantity": "{{strategy.order.contracts}}",
  "order_type": "MARKET"
}
```

### Alert 5: Decrease Position
**Condition:** Strategy reduces position (opposite direction but doesn't close)
**Message:**
```json
{
  "action": "decrease",
  "symbol": "BTCUSDT",
  "quantity": "{{strategy.order.contracts}}",
  "order_type": "MARKET"
}
```

## ✅ SOLUTION IMPLEMENTED: Strategy-Aware Endpoint

I've created a new endpoint `/webhook/tradingview-strategy` that automatically determines the correct action!

### Your TradingView Alert Template

**Use this exact template in your TradingView alert message:**

```json
{
  "order_action": "{{strategy.order.action}}",
  "symbol": "BTCUSDT",
  "contracts": "{{strategy.order.contracts}}",
  "position_size": "{{strategy.position_size}}",
  "order_type": "MARKET"
}
```

### Webhook URL

Set your TradingView webhook URL to:
```
https://your-domain.com/webhook/tradingview-strategy
```

### How It Works

The endpoint automatically:
1. Fetches your current position from AsterDEX
2. Compares with the incoming strategy order
3. Determines the correct action (open/close/increase/decrease)
4. Executes the trade

### Example Scenarios:

| Current Position | Order Action | Contracts | New Position | What Happens |
|-----------------|--------------|-----------|--------------|--------------|
| 0 | buy | 0.575181 | 0.575181 | **Opens** long position |
| 0.575181 | sell | 0.575181 | 0 | **Closes** position |
| 0.575181 | sell | 0.152568 | 0.422613 | **Decreases** position |
| 0 | sell | 0.30691 | -0.30691 | **Opens** short position |
| -0.30691 | buy | 0.30691 | 0 | **Closes** position |
| 0.575181 | buy | 0.2 | 0.775181 | **Increases** position |
| 0.575181 | sell | 0.8 | -0.225 | **Closes** + **Opens** short (flip) |

### Symbol Mapping

**Important:** Your TradingView shows `BTCUSDT.P` but AsterDEX uses `BTCUSDT`.

Change your template to:
```json
{
  "order_action": "{{strategy.order.action}}",
  "symbol": "BTCUSDT",
  "contracts": "{{strategy.order.contracts}}",
  "position_size": "{{strategy.position_size}}",
  "order_type": "MARKET"
}
```

Or if you want to use the ticker variable and strip the `.P`:
- Unfortunately TradingView doesn't support string manipulation in webhooks
- You'll need to hardcode the symbol as shown above

### Complete Setup Steps

1. **Start your server** (if not already running)
   ```bash
   docker-compose up -d
   ```

2. **In TradingView:**
   - Open your strategy chart
   - Click Alert button
   - Set condition to trigger on strategy order fills
   - Enable "Webhook URL"
   - Enter: `https://your-domain.com/webhook/tradingview-strategy`
   - Paste the JSON template above in the Message field
   - Click Create

3. **Test it:**
   - Wait for your strategy to generate an order
   - Check server logs: `docker logs -f asterdex-api`
   - Verify position on AsterDEX

### Advantages of This Approach

✅ **Single Alert:** One alert handles all scenarios  
✅ **Automatic Logic:** No need to create separate alerts for each action  
✅ **Position Sync:** Always syncs with your actual AsterDEX position  
✅ **Handles Flips:** Automatically closes and reopens when position flips  
✅ **Simple Template:** Just copy and paste the JSON above
