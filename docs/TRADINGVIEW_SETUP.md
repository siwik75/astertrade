# TradingView Webhook Setup Guide

This guide shows you how to configure TradingView alerts to send webhook signals to your AsterDEX Trading API server.

## Prerequisites

- Your AsterDEX Trading API server must be running and publicly accessible
- You need a TradingView account with alert capabilities
- Your server URL (e.g., `https://your-domain.com` or use ngrok for testing)

## Quick Start

### 1. Get Your Webhook URL

Your webhook endpoint is:
```
https://your-domain.com/webhook/tradingview
```

For local testing with ngrok:
```bash
ngrok http 8000
# Use the HTTPS URL provided: https://abc123.ngrok.io/webhook/tradingview
```

### 2. Create Alert in TradingView

1. Open a chart in TradingView
2. Click the **Alert** button (clock icon) or press `Alt + A`
3. Configure your alert conditions
4. In the **Notifications** tab, enable **Webhook URL**
5. Paste your webhook URL
6. In the **Message** field, paste one of the JSON templates below

## Webhook Message Templates

### Template 1: Open Long Position (Market Order)

Use this to enter a long position at market price.

```json
{
  "action": "open",
  "symbol": "{{ticker}}",
  "side": "BUY",
  "quantity": "0.001",
  "order_type": "MARKET"
}
```

**Explanation:**
- `action`: "open" creates a new position
- `symbol`: `{{ticker}}` automatically uses the chart's symbol
- `side`: "BUY" for long, "SELL" for short
- `quantity`: Amount to trade (adjust based on your risk)
- `order_type`: "MARKET" executes immediately at current price

### Template 2: Open Short Position (Market Order)

Use this to enter a short position at market price.

```json
{
  "action": "open",
  "symbol": "{{ticker}}",
  "side": "SELL",
  "quantity": "0.001",
  "order_type": "MARKET"
}
```

### Template 3: Open Long Position (Limit Order)

Use this to enter a long position at a specific price.

```json
{
  "action": "open",
  "symbol": "{{ticker}}",
  "side": "BUY",
  "quantity": "0.001",
  "order_type": "LIMIT",
  "price": "{{close}}"
}
```

**TradingView Variables:**
- `{{close}}`: Current close price
- `{{open}}`: Current open price
- `{{high}}`: Current high price
- `{{low}}`: Current low price
- You can also use fixed values like `"price": "50000.00"`

### Template 4: Increase Existing Position

Use this to add to an existing position (same direction).

```json
{
  "action": "increase",
  "symbol": "{{ticker}}",
  "quantity": "0.001",
  "order_type": "MARKET"
}
```

**Note:** This will automatically match the direction of your existing position.

### Template 5: Decrease Position (Take Partial Profit)

Use this to reduce your position size.

```json
{
  "action": "decrease",
  "symbol": "{{ticker}}",
  "quantity": "0.0005",
  "order_type": "MARKET"
}
```

**Important:** Quantity must be less than or equal to your current position size.

### Template 6: Close Entire Position

Use this to exit your position completely.

```json
{
  "action": "close",
  "symbol": "{{ticker}}"
}
```

**Note:** No quantity needed - closes 100% of the position.

## Advanced Templates

### Dynamic Quantity Based on Price

Calculate quantity based on a fixed dollar amount:

```json
{
  "action": "open",
  "symbol": "{{ticker}}",
  "side": "BUY",
  "quantity": "{{plot_0}}",
  "order_type": "MARKET"
}
```

Then in your TradingView Pine Script, calculate the quantity:
```pine
//@version=5
indicator("Position Size Calculator", overlay=true)

// Fixed dollar amount to risk
riskAmount = input.float(100, "Risk Amount ($)")

// Calculate quantity based on current price
quantity = riskAmount / close

// Plot for webhook
plot(quantity, "Quantity", display=display.none)
```

### Conditional Entry with Stop Loss

Open position with specific entry and stop loss levels:

```json
{
  "action": "open",
  "symbol": "{{ticker}}",
  "side": "BUY",
  "quantity": "0.001",
  "order_type": "LIMIT",
  "price": "{{plot_0}}"
}
```

Pine Script example:
```pine
//@version=5
strategy("Entry with Levels", overlay=true)

// Your entry logic
entryPrice = ta.sma(close, 20)

// Plot for webhook
plot(entryPrice, "Entry Price", display=display.none)

// Create alert when condition is met
if ta.crossover(close, entryPrice)
    alert("Entry Signal", alert.freq_once_per_bar_close)
```

## Complete Trading Strategy Example

### Strategy: Simple Moving Average Crossover

This example shows a complete strategy with entry and exit signals.

#### Alert 1: Long Entry
**Condition:** When fast MA crosses above slow MA
**Message:**
```json
{
  "action": "open",
  "symbol": "{{ticker}}",
  "side": "BUY",
  "quantity": "0.001",
  "order_type": "MARKET"
}
```

#### Alert 2: Long Exit
**Condition:** When fast MA crosses below slow MA
**Message:**
```json
{
  "action": "close",
  "symbol": "{{ticker}}"
}
```

#### Alert 3: Short Entry
**Condition:** When fast MA crosses below slow MA
**Message:**
```json
{
  "action": "open",
  "symbol": "{{ticker}}",
  "side": "SELL",
  "quantity": "0.001",
  "order_type": "MARKET"
}
```

#### Alert 4: Short Exit
**Condition:** When fast MA crosses above slow MA
**Message:**
```json
{
  "action": "close",
  "symbol": "{{ticker}}"
}
```

## Symbol Mapping

Make sure your TradingView symbols match AsterDEX format:

| TradingView | AsterDEX | Template |
|-------------|----------|----------|
| BTCUSD | BTCUSDT | Use `"symbol": "BTCUSDT"` |
| ETHUSD | ETHUSDT | Use `"symbol": "ETHUSDT"` |
| SOLUSD | SOLUSDT | Use `"symbol": "SOLUSDT"` |

**Option 1:** Use fixed symbol names
```json
{
  "action": "open",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "quantity": "0.001"
}
```

**Option 2:** Use `{{ticker}}` and ensure chart symbol matches
- Set your TradingView chart to "BTCUSDT" (if available)
- Or use symbol mapping in your strategy

## Adding Webhook Secret (Recommended)

If you configured `WEBHOOK_SECRET` in your `.env` file, you need to add it as a custom header.

### In TradingView Alert Settings:

Unfortunately, TradingView doesn't support custom headers directly in the UI. You have two options:

**Option 1: Include in URL (Less Secure)**
```
https://your-domain.com/webhook/tradingview?secret=your-secret-token
```

Then modify your webhook endpoint to check query parameters.

**Option 2: Use a Proxy/Gateway**
Set up a simple proxy (like Cloudflare Workers or AWS API Gateway) that adds the header before forwarding to your server.

**Option 3: Disable Webhook Secret**
For testing or if your server is not publicly accessible, you can leave `WEBHOOK_SECRET` unset in your `.env` file.

## Testing Your Webhook

### Test with curl

Before setting up TradingView alerts, test your webhook manually:

```bash
# Test open position
curl -X POST https://your-domain.com/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{
    "action": "open",
    "symbol": "BTCUSDT",
    "side": "BUY",
    "quantity": "0.001",
    "order_type": "MARKET"
  }'

# Test close position
curl -X POST https://your-domain.com/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{
    "action": "close",
    "symbol": "BTCUSDT"
  }'
```

### Test with TradingView

1. Create a simple alert with a condition that will trigger immediately
2. Use one of the templates above
3. Check your server logs to see if the webhook was received:
   ```bash
   docker logs -f asterdex-api
   ```
4. Verify the trade was executed on AsterDEX

## Common Issues

### Issue 1: Webhook Not Triggering

**Symptoms:** Alert fires in TradingView but no trade executes

**Solutions:**
- Check server logs: `docker logs asterdex-api`
- Verify webhook URL is correct and publicly accessible
- Test URL in browser: `https://your-domain.com/health`
- Check TradingView alert history for error messages
- Ensure JSON format is valid (use a JSON validator)

### Issue 2: Invalid Symbol Error

**Symptoms:** `400 Bad Request` - Symbol not found

**Solutions:**
- Verify symbol format matches AsterDEX (e.g., "BTCUSDT" not "BTCUSD")
- Check available symbols: `GET /positions` or AsterDEX exchange info
- Use fixed symbol names instead of `{{ticker}}` for testing

### Issue 3: Insufficient Balance

**Symptoms:** Order rejected due to insufficient balance

**Solutions:**
- Check account balance: `GET /account/balance`
- Reduce quantity in webhook message
- Ensure you have enough margin for the position
- Check leverage settings

### Issue 4: Position Not Found

**Symptoms:** `404 Not Found` when trying to increase/decrease/close

**Solutions:**
- Verify you have an open position: `GET /positions/BTCUSDT`
- Check if position was already closed
- Ensure symbol name matches exactly
- Check if you're using the correct position side (LONG/SHORT)

## Best Practices

### 1. Start Small
- Begin with very small quantities for testing
- Gradually increase size once confident

### 2. Use Paper Trading First
- Test your strategy thoroughly before using real funds
- Verify all alerts trigger correctly

### 3. Monitor Your Positions
- Regularly check `GET /positions` endpoint
- Set up monitoring/alerting for your server
- Keep track of your PnL

### 4. Handle Network Issues
- The server automatically retries failed requests
- Consider implementing additional safety checks in your strategy
- Have a manual backup plan to close positions

### 5. Secure Your Webhook
- Always use HTTPS in production
- Set `WEBHOOK_SECRET` for additional security
- Don't expose your webhook URL publicly
- Monitor for unauthorized access attempts

### 6. Symbol Validation
- Always verify symbol format before going live
- Create a mapping table for your commonly traded pairs
- Test each symbol individually first

### 7. Position Sizing
- Calculate position size based on account balance
- Use proper risk management (1-2% per trade)
- Consider using dynamic quantity calculation

## Example: Complete Setup Walkthrough

### Step 1: Deploy Your Server

```bash
# Using Docker Compose
docker-compose up -d

# Verify it's running
curl http://localhost:8000/health
```

### Step 2: Expose to Internet (for testing)

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from ngrok.com

# Start ngrok
ngrok http 8000

# Note the HTTPS URL: https://abc123.ngrok.io
```

### Step 3: Create TradingView Alert

1. Open BTCUSDT chart on TradingView
2. Click Alert button
3. Set condition: "Crossing" → "Close" → "Crossing Up" → "Value" → "50000"
4. Enable "Webhook URL"
5. Enter: `https://abc123.ngrok.io/webhook/tradingview`
6. Message:
   ```json
   {
     "action": "open",
     "symbol": "BTCUSDT",
     "side": "BUY",
     "quantity": "0.001",
     "order_type": "MARKET"
   }
   ```
7. Click "Create"

### Step 4: Test the Alert

1. Wait for price to cross 50000 (or adjust to current price)
2. Check server logs:
   ```bash
   docker logs -f asterdex-api
   ```
3. Verify position opened:
   ```bash
   curl http://localhost:8000/positions/BTCUSDT
   ```

### Step 5: Create Exit Alert

1. Create another alert for exit condition
2. Use close message:
   ```json
   {
     "action": "close",
     "symbol": "BTCUSDT"
   }
   ```

## Additional Resources

- [TradingView Webhook Documentation](https://www.tradingview.com/support/solutions/43000529348-i-want-to-know-more-about-webhooks/)
- [TradingView Alert Variables](https://www.tradingview.com/support/solutions/43000531021-how-to-use-a-variable-value-in-alert/)
- [AsterDEX API Documentation](https://docs.asterdex.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Support

If you encounter issues:
1. Check server logs for detailed error messages
2. Test webhook manually with curl
3. Verify all environment variables are set correctly
4. Review the main README.md troubleshooting section
5. Check API documentation at `/docs` endpoint
