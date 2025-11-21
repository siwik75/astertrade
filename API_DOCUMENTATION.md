# AsterDEX Trading API - Complete API Documentation

This document provides comprehensive documentation for all API endpoints, including request/response formats, authentication flow, and error handling.

## Table of Contents

- [Authentication Flow](#authentication-flow)
- [Webhook Endpoints](#webhook-endpoints)
- [Position Management Endpoints](#position-management-endpoints)
- [Account Endpoints](#account-endpoints)
- [Order Endpoints](#order-endpoints)
- [Health Endpoints](#health-endpoints)
- [Error Responses](#error-responses)

## Authentication Flow

The AsterDEX Trading API uses Web3-based ECDSA signature authentication for all requests to the AsterDEX platform.

### Authentication Process

1. **Nonce Generation**: Current timestamp in microseconds
2. **Parameter Preparation**: Convert all parameters to strings and sort by ASCII order
3. **ABI Encoding**: Encode parameters with user address, signer address, and nonce
4. **Keccak Hashing**: Hash the encoded data using Keccak-256
5. **ECDSA Signing**: Sign the hash with the API wallet private key
6. **Request Submission**: Include user, signer, nonce, and signature in the request

### Authentication Parameters

All authenticated requests to AsterDEX include:

| Parameter | Type | Description |
|-----------|------|-------------|
| `user` | string | Main wallet address |
| `signer` | string | API wallet address |
| `nonce` | integer | Timestamp in microseconds |
| `signature` | string | ECDSA signature (hex format) |
| `timestamp` | integer | Request timestamp in milliseconds |
| `recvWindow` | integer | Request validity window (default: 5000ms) |

### Webhook Authentication

For TradingView webhooks, optional secret token validation is supported:

- **Header**: `X-Webhook-Secret`
- **Value**: Secret token configured in `WEBHOOK_SECRET` environment variable
- If configured, all webhook requests must include this header with the correct value

---

## Webhook Endpoints

### POST /webhook/tradingview

Receive TradingView webhook signals and execute trading actions.

#### Supported Actions

- `open`: Open a new position
- `increase`: Add to an existing position
- `decrease`: Reduce position size (partial close)
- `close`: Close entire position

#### Request Headers

```
Content-Type: application/json
X-Webhook-Secret: your-secret-token (optional, if configured)
```

#### Request Body

```json
{
  "action": "string",        // Required: open, increase, decrease, close
  "symbol": "string",        // Required: Trading pair (e.g., BTCUSDT)
  "side": "string",          // Required for 'open': BUY or SELL
  "quantity": "string",      // Required for open/increase/decrease: Order quantity
  "price": "string",         // Optional: Limit order price
  "order_type": "string"     // Optional: MARKET (default) or LIMIT
}
```

#### Action-Specific Requirements

##### Open Position

```json
{
  "action": "open",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "quantity": "0.001",
  "order_type": "MARKET"
}
```

**Required Fields**: `action`, `symbol`, `side`, `quantity`

**Optional Fields**: `price` (required if `order_type` is LIMIT), `order_type`

##### Increase Position

```json
{
  "action": "increase",
  "symbol": "BTCUSDT",
  "quantity": "0.001",
  "order_type": "MARKET"
}
```

**Required Fields**: `action`, `symbol`, `quantity`

**Optional Fields**: `price`, `order_type`

**Notes**: 
- Queries current position to determine side
- Returns 404 if no position exists
- Order side must match existing position

##### Decrease Position

```json
{
  "action": "decrease",
  "symbol": "BTCUSDT",
  "quantity": "0.0005",
  "order_type": "MARKET"
}
```

**Required Fields**: `action`, `symbol`, `quantity`

**Optional Fields**: `price`, `order_type`

**Notes**:
- Places reduce-only order
- Validates quantity doesn't exceed position size
- Returns 400 if quantity is too large

##### Close Position

```json
{
  "action": "close",
  "symbol": "BTCUSDT"
}
```

**Required Fields**: `action`, `symbol`

**Notes**:
- Closes entire position at market price
- Returns 404 if no position exists
- Uses closePosition parameter

#### Response Format

**Success Response (200 OK)**

```json
{
  "success": true,
  "message": "Position opened successfully",
  "order": {
    "order_id": 12345678,
    "symbol": "BTCUSDT",
    "side": "BUY",
    "type": "MARKET",
    "status": "FILLED",
    "quantity": "0.001",
    "price": null,
    "executed_qty": "0.001",
    "avg_price": "43250.50"
  },
  "position": {
    "symbol": "BTCUSDT",
    "position_side": "BOTH",
    "position_amt": "0.001",
    "entry_price": "43250.50",
    "mark_price": "43255.00",
    "unrealized_profit": "0.0045",
    "leverage": 10,
    "margin_type": "CROSSED",
    "liquidation_price": "39000.00"
  }
}
```

#### Error Responses

**Invalid Action (400 Bad Request)**

```json
{
  "error": "Invalid action",
  "detail": "Action must be one of: open, increase, decrease, close",
  "code": 400,
  "timestamp": 1699999999999
}
```

**Position Not Found (404 Not Found)**

```json
{
  "error": "Position not found",
  "detail": "No open position for symbol BTCUSDT",
  "code": 404,
  "timestamp": 1699999999999
}
```

**Invalid Webhook Secret (401 Unauthorized)**

```json
{
  "error": "Unauthorized",
  "detail": "Invalid webhook secret",
  "code": 401,
  "timestamp": 1699999999999
}
```

---

## Position Management Endpoints

### GET /positions

Get all open positions.

#### Request

```bash
curl http://localhost:8000/positions
```

#### Response (200 OK)

```json
[
  {
    "symbol": "BTCUSDT",
    "position_side": "BOTH",
    "position_amt": "0.001",
    "entry_price": "43250.50",
    "mark_price": "43255.00",
    "unrealized_profit": "0.0045",
    "leverage": 10,
    "margin_type": "CROSSED",
    "liquidation_price": "39000.00"
  },
  {
    "symbol": "ETHUSDT",
    "position_side": "BOTH",
    "position_amt": "-0.01",
    "entry_price": "2250.00",
    "mark_price": "2245.50",
    "unrealized_profit": "0.045",
    "leverage": 20,
    "margin_type": "ISOLATED",
    "liquidation_price": "2500.00"
  }
]
```

**Notes**:
- Returns empty array `[]` if no positions exist
- Only returns positions with non-zero `position_amt`
- Negative `position_amt` indicates short position

---

### GET /positions/{symbol}

Get position for a specific trading pair.

#### Request

```bash
curl http://localhost:8000/positions/BTCUSDT
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | string | Trading pair symbol (e.g., BTCUSDT) |

#### Response (200 OK)

```json
{
  "symbol": "BTCUSDT",
  "position_side": "BOTH",
  "position_amt": "0.001",
  "entry_price": "43250.50",
  "mark_price": "43255.00",
  "unrealized_profit": "0.0045",
  "leverage": 10,
  "margin_type": "CROSSED",
  "liquidation_price": "39000.00"
}
```

#### Error Response (404 Not Found)

```json
{
  "error": "Position not found",
  "detail": "No open position for symbol BTCUSDT",
  "code": 404,
  "timestamp": 1699999999999
}
```

---

### POST /positions/{symbol}/leverage

Update leverage for a specific trading pair.

#### Request

```bash
curl -X POST http://localhost:8000/positions/BTCUSDT/leverage \
  -H "Content-Type: application/json" \
  -d '{"leverage": 20}'
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | string | Trading pair symbol (e.g., BTCUSDT) |

#### Request Body

```json
{
  "leverage": 20
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `leverage` | integer | Yes | 1-125 | Leverage multiplier |

#### Response (200 OK)

```json
{
  "symbol": "BTCUSDT",
  "leverage": 20,
  "maxNotionalValue": "1000000"
}
```

#### Error Response (400 Bad Request)

```json
{
  "error": "Invalid leverage",
  "detail": "Leverage must be between 1 and 125",
  "code": 400,
  "timestamp": 1699999999999
}
```

---

### POST /positions/{symbol}/margin-type

Update margin type for a specific trading pair.

#### Request

```bash
curl -X POST http://localhost:8000/positions/BTCUSDT/margin-type \
  -H "Content-Type: application/json" \
  -d '{"margin_type": "ISOLATED"}'
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | string | Trading pair symbol (e.g., BTCUSDT) |

#### Request Body

```json
{
  "margin_type": "ISOLATED"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `margin_type` | string | Yes | ISOLATED or CROSSED | Margin mode |

#### Response (200 OK)

```json
{
  "symbol": "BTCUSDT",
  "marginType": "ISOLATED"
}
```

#### Error Response (400 Bad Request)

```json
{
  "error": "Invalid margin type",
  "detail": "Margin type must be ISOLATED or CROSSED",
  "code": 400,
  "timestamp": 1699999999999
}
```

**Notes**:
- Must close all positions before changing margin type
- ISOLATED: Each position has separate margin
- CROSSED: All positions share account margin

---

## Account Endpoints

### GET /account/balance

Get account balance information with 5-second caching.

#### Request

```bash
curl http://localhost:8000/account/balance
```

#### Response (200 OK)

```json
[
  {
    "asset": "USDT",
    "wallet_balance": "10000.50",
    "available_balance": "9500.25",
    "cross_wallet_balance": "10000.50",
    "unrealized_profit": "45.75"
  }
]
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `asset` | string | Asset symbol (e.g., USDT) |
| `wallet_balance` | string | Total wallet balance |
| `available_balance` | string | Available balance for trading |
| `cross_wallet_balance` | string | Cross margin wallet balance |
| `unrealized_profit` | string | Unrealized profit/loss from open positions |

**Notes**:
- Balance is cached for 5 seconds to reduce API calls
- All amounts are returned as strings to preserve precision

---

### GET /account/info

Get comprehensive account information including positions, balances, and settings.

#### Request

```bash
curl http://localhost:8000/account/info
```

#### Response (200 OK)

```json
{
  "feeTier": 0,
  "canTrade": true,
  "canDeposit": true,
  "canWithdraw": true,
  "updateTime": 1699999999999,
  "totalInitialMargin": "500.00",
  "totalMaintMargin": "250.00",
  "totalWalletBalance": "10000.50",
  "totalUnrealizedProfit": "45.75",
  "totalMarginBalance": "10046.25",
  "totalPositionInitialMargin": "500.00",
  "totalOpenOrderInitialMargin": "0.00",
  "totalCrossWalletBalance": "10000.50",
  "totalCrossUnPnl": "45.75",
  "availableBalance": "9500.25",
  "maxWithdrawAmount": "9500.25",
  "assets": [
    {
      "asset": "USDT",
      "walletBalance": "10000.50",
      "unrealizedProfit": "45.75",
      "marginBalance": "10046.25",
      "maintMargin": "250.00",
      "initialMargin": "500.00",
      "positionInitialMargin": "500.00",
      "openOrderInitialMargin": "0.00",
      "crossWalletBalance": "10000.50",
      "crossUnPnl": "45.75",
      "availableBalance": "9500.25",
      "maxWithdrawAmount": "9500.25"
    }
  ],
  "positions": [
    {
      "symbol": "BTCUSDT",
      "initialMargin": "432.50",
      "maintMargin": "216.25",
      "unrealizedProfit": "4.50",
      "positionInitialMargin": "432.50",
      "openOrderInitialMargin": "0.00",
      "leverage": "10",
      "isolated": false,
      "entryPrice": "43250.00",
      "maxNotional": "1000000",
      "positionSide": "BOTH",
      "positionAmt": "0.001"
    }
  ]
}
```

**Notes**:
- Provides complete account snapshot
- Includes all assets and positions
- Use for comprehensive account monitoring

---

## Order Endpoints

### GET /orders

Get order history with optional filters.

#### Request

```bash
# Get all orders for a symbol
curl "http://localhost:8000/orders?symbol=BTCUSDT&limit=50"

# Get orders within time range
curl "http://localhost:8000/orders?symbol=BTCUSDT&startTime=1699900000000&endTime=1699999999999&limit=100"
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | string | No | Trading pair symbol (e.g., BTCUSDT) |
| `startTime` | integer | No | Start time in milliseconds |
| `endTime` | integer | No | End time in milliseconds |
| `limit` | integer | No | Number of orders to return (default: 50, max: 1000) |

#### Response (200 OK)

```json
[
  {
    "order_id": 12345678,
    "symbol": "BTCUSDT",
    "side": "BUY",
    "type": "MARKET",
    "status": "FILLED",
    "quantity": "0.001",
    "price": null,
    "executed_qty": "0.001",
    "avg_price": "43250.50"
  },
  {
    "order_id": 12345679,
    "symbol": "BTCUSDT",
    "side": "SELL",
    "type": "LIMIT",
    "status": "CANCELED",
    "quantity": "0.001",
    "price": "44000.00",
    "executed_qty": "0.000",
    "avg_price": null
  }
]
```

#### Order Status Values

| Status | Description |
|--------|-------------|
| `NEW` | Order accepted but not yet filled |
| `PARTIALLY_FILLED` | Order partially executed |
| `FILLED` | Order completely executed |
| `CANCELED` | Order canceled by user |
| `REJECTED` | Order rejected by exchange |
| `EXPIRED` | Order expired (time in force) |

**Notes**:
- Returns orders sorted by time (newest first)
- If no symbol specified, returns orders for all symbols
- Time range is inclusive

---

### GET /orders/open

Get all currently open orders.

#### Request

```bash
# All open orders
curl http://localhost:8000/orders/open

# Open orders for specific symbol
curl "http://localhost:8000/orders/open?symbol=BTCUSDT"
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | string | No | Trading pair symbol (e.g., BTCUSDT) |

#### Response (200 OK)

```json
[
  {
    "order_id": 12345680,
    "symbol": "BTCUSDT",
    "side": "BUY",
    "type": "LIMIT",
    "status": "NEW",
    "quantity": "0.001",
    "price": "42000.00",
    "executed_qty": "0.000",
    "avg_price": null
  }
]
```

**Notes**:
- Returns only orders with status NEW or PARTIALLY_FILLED
- Returns empty array if no open orders exist

---

## Health Endpoints

### GET /

Root endpoint that redirects to interactive API documentation.

#### Request

```bash
curl http://localhost:8000/
```

#### Response (307 Temporary Redirect)

Redirects to `/docs`

---

### GET /health

Health check endpoint to verify server status.

#### Request

```bash
curl http://localhost:8000/health
```

#### Response (200 OK)

```json
{
  "status": "healthy",
  "timestamp": 1699999999999,
  "version": "1.0.0"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Server status (healthy/unhealthy) |
| `timestamp` | integer | Current server timestamp in milliseconds |
| `version` | string | API version |

**Notes**:
- Use for monitoring and load balancer health checks
- Returns 200 if server is operational
- Validates configuration is loaded

---

## Error Responses

All error responses follow a consistent format for easy parsing and handling.

### Error Response Format

```json
{
  "error": "Error type",
  "detail": "Detailed error message",
  "code": 400,
  "timestamp": 1699999999999
}
```

### HTTP Status Codes

| Code | Description | Common Causes |
|------|-------------|---------------|
| 400 | Bad Request | Invalid parameters, validation errors |
| 401 | Unauthorized | Invalid webhook secret, missing authentication |
| 404 | Not Found | Position not found, order not found |
| 422 | Unprocessable Entity | Pydantic validation errors |
| 429 | Too Many Requests | Rate limit exceeded (auto-retried) |
| 500 | Internal Server Error | Server-side errors |
| 502 | Bad Gateway | AsterDEX API unavailable |
| 504 | Gateway Timeout | Request timeout, AsterDEX API slow |

### Common Error Examples

#### Validation Error (422)

```json
{
  "detail": [
    {
      "loc": ["body", "quantity"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### AsterDEX API Error (400)

```json
{
  "error": "AsterDEX API Error",
  "detail": "Insufficient balance",
  "code": -2019,
  "timestamp": 1699999999999
}
```

#### Rate Limit Error (429)

```json
{
  "error": "Rate limit exceeded",
  "detail": "Too many requests. Please try again later.",
  "code": 429,
  "timestamp": 1699999999999
}
```

**Notes**:
- Server automatically retries rate limit errors with exponential backoff
- Original AsterDEX error codes are preserved in the response
- All errors include timestamp for debugging

#### Timeout Error (504)

```json
{
  "error": "Gateway timeout",
  "detail": "Request to AsterDEX API timed out after 30 seconds",
  "code": 504,
  "timestamp": 1699999999999
}
```

#### Position Not Found (404)

```json
{
  "error": "Position not found",
  "detail": "No open position for symbol BTCUSDT",
  "code": 404,
  "timestamp": 1699999999999
}
```

---

## Best Practices

### 1. Error Handling

- Always check the `success` field in webhook responses
- Implement retry logic for 429 and 5xx errors (server does this automatically)
- Log error details including `code` and `timestamp` for debugging

### 2. Position Management

- Query current position before increase/decrease operations
- Validate quantity doesn't exceed position size for decrease operations
- Use the `/positions/{symbol}` endpoint to check position status

### 3. Order Execution

- Use MARKET orders for immediate execution
- Use LIMIT orders for price control
- Monitor order status using `/orders/open` endpoint

### 4. Rate Limiting

- The server implements automatic retry with exponential backoff
- Avoid excessive webhook triggers from TradingView
- Cache balance information (automatically cached for 5 seconds)

### 5. Security

- Always use HTTPS in production
- Set `WEBHOOK_SECRET` and validate it in TradingView
- Never expose your private key or API credentials
- Rotate API credentials periodically

### 6. Monitoring

- Use `/health` endpoint for uptime monitoring
- Monitor logs for errors and warnings
- Track order success/failure rates
- Monitor unrealized profit/loss regularly

---

## Interactive Documentation

For interactive API testing and exploration, visit the auto-generated Swagger UI:

**URL**: `http://your-server:8000/docs`

Features:
- Try out all endpoints directly from the browser
- View detailed request/response schemas
- See example payloads for all endpoints
- Test authentication and error scenarios

---

## Support

For additional help:
- Review the main [README.md](README.md) for setup instructions
- Check the [Troubleshooting](README.md#troubleshooting) section
- Consult AsterDEX API documentation for platform-specific details
- Review server logs for detailed error information

