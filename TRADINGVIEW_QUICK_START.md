# 🚀 TradingView Quick Start - Your Strategy

## Your Exact Template

Copy this into your TradingView alert message:

```json
{
  "order_action": "{{strategy.order.action}}",
  "symbol": "BTCUSDT",
  "contracts": "{{strategy.order.contracts}}",
  "position_size": "{{strategy.position_size}}",
  "order_type": "MARKET"
}
```

## Webhook URL

```
https://your-domain.com/webhook/tradingview-strategy
```

## Setup in TradingView

1. Open your "Regime-Filtered Trend Breakout v6" strategy chart
2. Click the **Alert** button (⏰ icon)
3. Set **Condition** to: "Order fills only" or "Any alert() function call"
4. Enable **Webhook URL**
5. Paste your webhook URL
6. In **Message** field, paste the JSON template above
7. Click **Create**

## What It Does

Your strategy generates orders like:
- ✅ `buy @ 0.575181` → Bot opens long position
- ✅ `sell @ 0.152568` → Bot reduces/closes position
- ✅ `sell @ 0.30691` → Bot opens short position
- ✅ `buy @ 0.30691` → Bot closes short position

The bot automatically figures out whether to:
- **Open** a new position
- **Close** an existing position
- **Increase** position size
- **Decrease** position size
- **Flip** from long to short (or vice versa)

## Important Notes

### Symbol Name
Your TradingView shows `BTCUSDT.P` but use `BTCUSDT` in the template (without `.P`)

### For Different Symbols
Change the symbol in the template:
```json
{
  "order_action": "{{strategy.order.action}}",
  "symbol": "ETHUSDT",
  "contracts": "{{strategy.order.contracts}}",
  "position_size": "{{strategy.position_size}}",
  "order_type": "MARKET"
}
```

### Multiple Symbols
Create separate alerts for each symbol with different templates.

## Testing

### 1. Test Server is Running
```bash
curl https://your-domain.com/health
```

### 2. Test Webhook Manually
```bash
curl -X POST https://your-domain.com/webhook/tradingview-strategy \
  -H "Content-Type: application/json" \
  -d '{
    "order_action": "buy",
    "symbol": "BTCUSDT",
    "contracts": "0.001",
    "position_size": "0.001",
    "order_type": "MARKET"
  }'
```

### 3. Check Logs
```bash
docker logs -f asterdex-api
```

## Troubleshooting

### Alert Not Triggering
- Check alert is active in TradingView
- Verify webhook URL is correct
- Check server logs for incoming requests

### Wrong Symbol Error
- Make sure symbol is `BTCUSDT` not `BTCUSDT.P`
- Verify symbol exists on AsterDEX

### Position Mismatch
- The bot syncs with your actual AsterDEX position
- If positions are out of sync, close manually and let strategy reopen

## Next Steps

1. ✅ Copy the JSON template
2. ✅ Create alert in TradingView
3. ✅ Test with small position size first
4. ✅ Monitor logs to verify it's working
5. ✅ Gradually increase position size

## Support

- Full documentation: `docs/TRADINGVIEW_STRATEGY_TEMPLATE.md`
- API docs: `https://your-domain.com/docs`
- Check logs: `docker logs asterdex-api`
