# Apply Fix Right Now

## One-Line Command

SSH into your droplet and run:

```bash
cd /opt/asterdex-trading-api && git pull && bash .digitalocean/fix-nginx-routes.sh && docker compose restart && echo "✅ Fix applied! Test with: curl http://localhost:8000/health"
```

## Or Step-by-Step

```bash
# 1. SSH
ssh root@46.101.196.30

# 2. Navigate
cd /opt/asterdex-trading-api

# 3. Pull changes
git pull

# 4. Fix nginx
bash .digitalocean/fix-nginx-routes.sh

# 5. Restart app
docker compose restart

# 6. Test
curl http://localhost:8000/health
curl -H "X-API-Key: $(grep API_KEY .env | cut -d= -f2)" http://localhost:8000/positions
```

## What This Does

1. **Pulls latest code** with updated nginx configuration
2. **Fixes nginx routes** to include `/positions`, `/account`, `/orders`
3. **Restarts application** to update OpenAPI spec with security scheme
4. **Tests** that everything works

## After Running

### Test in Browser

1. Visit: `http://astertrade.ai/docs`
2. You should see:
   - "Authorize" button at top right
   - Lock icons (🔒) next to protected endpoints
   - All endpoints visible (positions, account, orders)

### Test with curl

```bash
# Should work (public)
curl http://astertrade.ai/health

# Should fail with 403 (protected, no key)
curl http://astertrade.ai/positions

# Should work (protected, with key)
curl -H "X-API-Key: your-key" http://astertrade.ai/positions
```

## If It Doesn't Work

See [FIX_ROUTES_AND_SWAGGER.md](FIX_ROUTES_AND_SWAGGER.md) for troubleshooting.
