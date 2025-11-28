# API Key Quick Reference

## Generate Key

```bash
python generate_api_key.py
```

## Add to .env

```bash
API_KEY=your-generated-key-here
```

## Restart

```bash
docker compose restart
```

## Use in Requests

### curl
```bash
curl -H "X-API-Key: your-key" http://localhost:8000/positions
```

### Python
```python
import requests

headers = {"X-API-Key": "your-key"}
response = requests.get("http://localhost:8000/positions", headers=headers)
```

### JavaScript
```javascript
fetch('http://localhost:8000/positions', {
  headers: {'X-API-Key': 'your-key'}
})
```

## Protected Endpoints

Require `X-API-Key` header:
- `/positions`
- `/positions/{symbol}`
- `/account/balance`
- `/account/info`
- `/orders`
- `/orders/open`

## Public Endpoints

No authentication needed:
- `/` (welcome page)
- `/health`
- `/docs`

## Webhook Endpoints

Use `X-Webhook-Secret` header (not API key):
- `/webhook/tradingview`

## Error Responses

### 401 - Missing Key
```json
{"detail": "API key is required. Provide it in the X-API-Key header."}
```

### 403 - Invalid Key
```json
{"detail": "Invalid API key"}
```

## Swagger UI

1. Go to `/docs`
2. Click "Authorize" button
3. Enter your API key
4. Click "Authorize"
5. Test endpoints

## Full Documentation

- [SECURITY_SETUP.md](SECURITY_SETUP.md) - Setup guide
- [API_SECURITY.md](API_SECURITY.md) - Complete documentation
