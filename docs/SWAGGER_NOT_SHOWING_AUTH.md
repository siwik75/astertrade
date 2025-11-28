# Troubleshooting: Swagger Not Showing Authentication

## Problem

After adding API key authentication and restarting the application, the Swagger UI at `/docs` still doesn't show:
- Lock icons (🔒) on protected endpoints
- "Authorize" button

## Root Cause

**Browser caching** - The browser has cached the old OpenAPI spec and Swagger UI assets.

## Verification

First, verify the OpenAPI spec is correct:

```bash
# Check the OpenAPI JSON directly
curl http://localhost:8000/openapi.json | python -m json.tool | grep -A 10 "securitySchemes"
```

You should see:
```json
"securitySchemes": {
  "APIKeyHeader": {
    "type": "apiKey",
    "description": "API key for accessing protected endpoints...",
    "in": "header",
    "name": "X-API-Key"
  }
}
```

If you see this, the backend is correct - it's a browser caching issue.

## Solutions

### Solution 1: Hard Refresh (Quickest)

**Windows/Linux:**
- Chrome/Edge: `Ctrl + Shift + R` or `Ctrl + F5`
- Firefox: `Ctrl + Shift + R` or `Ctrl + F5`

**Mac:**
- Chrome/Edge: `Cmd + Shift + R`
- Firefox: `Cmd + Shift + R`
- Safari: `Cmd + Option + R`

### Solution 2: Clear Browser Cache

**Chrome/Edge:**
1. Press `Ctrl + Shift + Delete` (Windows) or `Cmd + Shift + Delete` (Mac)
2. Select "Cached images and files"
3. Click "Clear data"
4. Refresh the page

**Firefox:**
1. Press `Ctrl + Shift + Delete` (Windows) or `Cmd + Shift + Delete` (Mac)
2. Select "Cache"
3. Click "Clear Now"
4. Refresh the page

**Safari:**
1. Go to Safari → Preferences → Advanced
2. Check "Show Develop menu in menu bar"
3. Go to Develop → Empty Caches
4. Refresh the page

### Solution 3: Incognito/Private Window

Open `/docs` in an incognito/private window:

**Chrome/Edge:**
- Windows/Linux: `Ctrl + Shift + N`
- Mac: `Cmd + Shift + N`

**Firefox:**
- Windows/Linux: `Ctrl + Shift + P`
- Mac: `Cmd + Shift + P`

**Safari:**
- Mac: `Cmd + Shift + N`

### Solution 4: Disable Cache in DevTools

1. Open DevTools:
   - Windows/Linux: `F12` or `Ctrl + Shift + I`
   - Mac: `Cmd + Option + I`

2. Go to Network tab

3. Check "Disable cache"

4. Keep DevTools open and refresh the page

### Solution 5: Clear Site Data

**Chrome/Edge:**
1. Click the lock icon (or "Not secure") in the address bar
2. Click "Site settings"
3. Click "Clear data"
4. Refresh the page

**Firefox:**
1. Click the lock icon in the address bar
2. Click "Clear cookies and site data"
3. Confirm
4. Refresh the page

### Solution 6: Force Reload OpenAPI Spec

Visit the OpenAPI spec directly to force reload:

1. Go to: `http://your-domain/openapi.json`
2. Hard refresh: `Ctrl + Shift + R` (or `Cmd + Shift + R` on Mac)
3. Go back to: `http://your-domain/docs`
4. Hard refresh again

### Solution 7: Add Cache Buster

Add a query parameter to force reload:

```
http://your-domain/docs?v=2
```

Or:

```
http://your-domain/docs?nocache=true
```

### Solution 8: Restart Browser

Close all browser windows and restart the browser completely.

## Verification After Fix

After trying the solutions above, you should see:

### 1. Authorize Button

At the top right of `/docs`, you should see a button with a lock icon (🔓) labeled "Authorize".

### 2. Lock Icons on Endpoints

Protected endpoints should show a lock icon:

```
Positions
  🔒 GET  /positions              Get All Open Positions
  🔒 GET  /positions/{symbol}     Get Position by Symbol

Account
  🔒 GET  /account/balance        Get Account Balance
  🔒 GET  /account/info           Get Full Account Information

Orders
  🔒 GET  /orders                 Get Order History
  🔒 GET  /orders/open            Get Open Orders

Health
     GET  /health                 Health Check (no lock - public)
```

### 3. Security Scheme in Endpoint Details

When you expand an endpoint (e.g., `/positions`), you should see:

```
Security:
  APIKeyHeader (apiKey)
```

## Still Not Working?

### Check 1: Verify Application Restarted

```bash
# On droplet
docker compose ps

# Should show "Up" status
# If not, restart:
docker compose restart
```

### Check 2: Verify Code is Updated

```bash
# On droplet
cd /opt/asterdex-trading-api
git log --oneline -5

# Should show recent commits with security changes
```

### Check 3: Check OpenAPI Spec

```bash
curl http://localhost:8000/openapi.json | grep -c "securitySchemes"

# Should return: 1 (or higher)
# If returns: 0, the code isn't updated
```

### Check 4: Check Application Logs

```bash
docker compose logs --tail=50 | grep -i security
docker compose logs --tail=50 | grep -i api_key
```

### Check 5: Test with curl

```bash
# Test that security is actually working
curl http://localhost:8000/positions

# Should return:
# {"detail":"API key is required. Provide it in the X-API-Key header."}
```

### Check 6: Try Different Browser

If one browser doesn't work, try a different one:
- Chrome
- Firefox
- Edge
- Safari

### Check 7: Check Browser Console

1. Open DevTools (`F12`)
2. Go to Console tab
3. Look for errors related to:
   - CORS
   - Loading resources
   - JavaScript errors

## Common Issues

### Issue: "Authorize button appears but doesn't work"

**Solution:** JavaScript error. Check browser console for errors.

### Issue: "Lock icons appear but clicking them does nothing"

**Solution:** Clear browser cache and hard refresh.

### Issue: "Everything works in incognito but not in regular window"

**Solution:** Clear site data for your domain in regular browser.

### Issue: "Works on localhost but not on domain"

**Solution:** 
1. Check nginx is proxying correctly
2. Clear browser cache for the domain
3. Try accessing via IP address

## Prevention

To avoid this issue in the future:

### 1. Always Hard Refresh After Updates

After deploying changes, always do a hard refresh:
- `Ctrl + Shift + R` (Windows/Linux)
- `Cmd + Shift + R` (Mac)

### 2. Use Incognito for Testing

When testing new features, use incognito mode to avoid cache issues.

### 3. Disable Cache During Development

Keep DevTools open with "Disable cache" checked when developing.

### 4. Version Your API

Add version numbers to your API URL:
- `http://your-domain/v1/docs`
- `http://your-domain/v2/docs`

## Summary

The most common solution is a **hard refresh**:
- Windows/Linux: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

If that doesn't work, try an **incognito window**.

If neither works, verify the backend is actually updated by checking the OpenAPI spec directly:
```bash
curl http://your-domain/openapi.json | grep securitySchemes
```

## Related Documentation

- [SWAGGER_AUTH_GUIDE.md](SWAGGER_AUTH_GUIDE.md) - How to use Swagger with authentication
- [API_SECURITY.md](API_SECURITY.md) - Complete security documentation
- [FIX_ROUTES_AND_SWAGGER.md](../.digitalocean/FIX_ROUTES_AND_SWAGGER.md) - Fixing routes and Swagger
