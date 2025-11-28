# Fix Missing Routes and Swagger Documentation

## Issues

1. **404 errors** when accessing `/account`, `/positions`, `/orders` endpoints
2. **No lock icons** in Swagger documentation at `/docs`

## Root Causes

1. **Nginx configuration** was missing routes for `/positions`, `/account`, `/orders`
2. **Application not restarted** after security changes

## Quick Fix (Run on Droplet)

```bash
# SSH into your droplet
ssh root@46.101.196.30

# Navigate to app directory
cd /opt/asterdex-trading-api

# Pull latest changes
git pull

# Fix nginx configuration
bash .digitalocean/fix-nginx-routes.sh

# Restart application (to update OpenAPI spec)
docker compose restart

# Wait a few seconds
sleep 5

# Test
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## What Gets Fixed

### 1. Nginx Routes

**Before:**
```nginx
location ~ ^/(docs|health|openapi.json|webhook) {
    # Only these 4 routes worked
}
```

**After:**
```nginx
location ~ ^/(docs|redoc|health|openapi.json|webhook|positions|account|orders) {
    # All API routes now work
}
```

### 2. Swagger Documentation

**Before:**
- No lock icons on protected endpoints
- No "Authorize" button

**After:**
- Lock icons (🔒) on protected endpoints
- "Authorize" button visible
- Security scheme in OpenAPI spec

## Verification

### Test 1: Check Routes Work

```bash
# Health check (public)
curl http://astertrade.ai/health
# Should return: {"status":"healthy",...}

# Docs (public)
curl http://astertrade.ai/docs
# Should return: HTML page

# Positions (protected - should fail without key)
curl http://astertrade.ai/positions
# Should return: {"detail":"Invalid API key"}

# Positions (protected - should work with key)
curl -H "X-API-Key: your-key" http://astertrade.ai/positions
# Should return: [...]
```

### Test 2: Check Swagger UI

1. Visit: `http://astertrade.ai/docs`
2. Look for:
   - ✅ "Authorize" button at top right (🔓)
   - ✅ Lock icons (🔒) next to protected endpoints
   - ✅ `/positions` endpoint visible
   - ✅ `/account/balance` endpoint visible
   - ✅ `/orders` endpoint visible

### Test 3: Test Authentication in Swagger

1. Click "Authorize" button
2. Enter your API key
3. Click "Authorize"
4. Try executing `/account/balance`
5. Should work and return your balance

## Manual Fix (If Script Fails)

### Fix Nginx Manually

```bash
# SSH into droplet
ssh root@46.101.196.30

# Edit nginx config
sudo nano /etc/nginx/sites-available/asterdex-api
```

Find this line:
```nginx
location ~ ^/(docs|health|openapi.json|webhook) {
```

Change it to:
```nginx
location ~ ^/(docs|redoc|health|openapi.json|webhook|positions|account|orders) {
```

Save and exit (Ctrl+X, Y, Enter), then:

```bash
# Test config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Restart Application Manually

```bash
cd /opt/asterdex-trading-api
docker compose restart
```

## Troubleshooting

### Still Getting 404

**Check nginx is running:**
```bash
sudo systemctl status nginx
```

**Check nginx config:**
```bash
sudo nginx -t
sudo cat /etc/nginx/sites-available/asterdex-api | grep "location ~"
```

**Check nginx logs:**
```bash
sudo tail -f /var/log/nginx/error.log
```

### Still No Lock Icons in Swagger

**Check app is running:**
```bash
docker compose ps
```

**Restart app:**
```bash
docker compose restart
```

**Check app logs:**
```bash
docker compose logs -f
```

**Clear browser cache:**
- Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- Or use incognito/private window

**Check OpenAPI spec:**
```bash
curl http://localhost:8000/openapi.json | grep -A 5 "securitySchemes"
```

Should show:
```json
"securitySchemes": {
  "X-API-Key": {
    "type": "apiKey",
    "in": "header",
    "name": "X-API-Key"
  }
}
```

### API Key Not Working

**Check .env file:**
```bash
cat .env | grep API_KEY
```

**Generate new key if needed:**
```bash
python generate_api_key.py
```

**Update .env:**
```bash
nano .env
# Add: API_KEY=your-new-key
```

**Restart:**
```bash
docker compose restart
```

## Complete Fix Workflow

```bash
# 1. SSH into droplet
ssh root@46.101.196.30

# 2. Navigate to app
cd /opt/asterdex-trading-api

# 3. Pull latest code
git pull

# 4. Fix nginx routes
bash .digitalocean/fix-nginx-routes.sh

# 5. Restart app
docker compose restart

# 6. Wait for app to start
sleep 10

# 7. Test health
curl http://localhost:8000/health

# 8. Test docs
curl http://localhost:8000/docs | head -20

# 9. Test protected endpoint (should fail)
curl http://localhost:8000/positions

# 10. Test with API key (should work)
curl -H "X-API-Key: $(grep API_KEY .env | cut -d= -f2)" \
  http://localhost:8000/positions
```

## Expected Results

### Before Fix

```bash
curl http://astertrade.ai/account/balance
# 404 Not Found (nginx error)
```

### After Fix

```bash
curl http://astertrade.ai/account/balance
# {"detail":"Invalid API key"} (FastAPI error - correct!)

curl -H "X-API-Key: your-key" http://astertrade.ai/account/balance
# [{"asset":"USDT",...}] (Success!)
```

## Summary

The fix involves:
1. ✅ Update nginx config to include `/positions`, `/account`, `/orders` routes
2. ✅ Restart application to update OpenAPI spec
3. ✅ Clear browser cache to see updated Swagger UI

After these steps:
- All API endpoints will be accessible
- Swagger UI will show lock icons
- Authentication will work properly

## Need Help?

If you're still having issues:

1. Check nginx logs: `sudo tail -50 /var/log/nginx/error.log`
2. Check app logs: `docker compose logs --tail=50`
3. Verify routes: `curl -v http://localhost:8000/positions`
4. Test locally: `curl http://localhost:8000/health`
