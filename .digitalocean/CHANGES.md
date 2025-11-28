# Deployment Configuration Changes

## Summary

Updated the droplet setup to include a welcome page and improved nginx configuration that handles both domain and IP requests consistently.

## What Changed

### 1. New Files Created
- ✅ `.digitalocean/welcome.html` - Beautiful welcome page for the service
- ✅ `.digitalocean/nginx.conf` - Updated nginx configuration template
- ✅ `.digitalocean/update-nginx-welcome.sh` - Quick update script for existing droplets
- ✅ `.digitalocean/QUICK_UPDATE.md` - Guide for updating existing deployments
- ✅ `.digitalocean/CHANGES.md` - This file

### 2. Updated Files
- ✅ `.digitalocean/droplet-setup.sh` - Now idempotent and includes welcome page setup
- ✅ `.digitalocean/README.md` - Added quick commands section

## Key Improvements

### Idempotent Setup Script
The `droplet-setup.sh` script is now safe to run multiple times:
- Checks if Docker is already installed before installing
- Checks if repository is already cloned before cloning
- Won't overwrite existing `.env` file
- Updates nginx config to latest version
- Updates welcome page to latest version

### Welcome Page
- Professional landing page at root URL (`/`)
- Shows service status and features
- Links to API documentation and health check
- Responsive design
- Matches your branding

### Improved Nginx Configuration
- Handles both domain (`astertrade.ai`) and IP (`46.101.196.30`) consistently
- Serves welcome page at root
- API endpoints still accessible at `/docs`, `/health`, `/webhook`
- Optional `/api/*` prefix for all API endpoints
- Proper timeouts configured
- Default server to catch all requests

## URL Structure

### Before
```
/                    → FastAPI docs (via IP) or nginx default (via domain)
/docs                → FastAPI interactive docs
/health              → Health check endpoint
/webhook/tradingview → TradingView webhook
```

### After
```
/                    → Welcome page (both domain and IP)
/docs                → FastAPI interactive docs
/health              → Health check endpoint
/webhook/tradingview → TradingView webhook
/api/*               → Optional API prefix (proxies to FastAPI)
```

## How to Apply Changes

### For New Droplets
```bash
bash .digitalocean/droplet-setup.sh
```

### For Existing Droplets
```bash
# Quick update (recommended)
bash .digitalocean/update-nginx-welcome.sh

# Or full setup (also safe)
bash .digitalocean/droplet-setup.sh
```

See [QUICK_UPDATE.md](QUICK_UPDATE.md) for detailed instructions.

## Configuration Details

### Nginx Server Block
```nginx
server {
    listen 80 default_server;
    server_name astertrade.ai www.astertrade.ai 46.101.196.30 _;
    
    location = / {
        # Welcome page
    }
    
    location /api/ {
        # API endpoints with /api prefix
    }
    
    location ~ ^/(docs|health|openapi.json|webhook) {
        # Direct API access
    }
}
```

### Welcome Page Location
- File: `/var/www/asterdex/index.html`
- Served by: nginx directly (not proxied to FastAPI)
- Can be customized by editing the file

### Domain Configuration
- Stored in: `/etc/nginx/.asterdex-domain`
- Used by scripts to remember your domain
- Can be updated by editing the file or re-running scripts

## Benefits

1. **Consistent Experience**: Both domain and IP show the same content
2. **Professional Look**: Welcome page instead of raw API docs
3. **Better UX**: Clear navigation to API docs and health check
4. **Maintainable**: Idempotent scripts make updates easy
5. **Flexible**: Can customize welcome page without touching code
6. **Safe**: Backups created before updates

## Testing

After applying changes, verify:

```bash
# Welcome page
curl http://astertrade.ai/
curl http://46.101.196.30/

# API endpoints
curl http://astertrade.ai/health
curl http://astertrade.ai/docs

# Webhook (should still work)
curl -X POST http://astertrade.ai/webhook/tradingview \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secret" \
  -d '{"action":"buy","symbol":"BTCUSDT"}'
```

## Rollback

If needed, restore previous nginx config:

```bash
# List backups
ls -la /etc/nginx/sites-available/asterdex-api.backup.*

# Restore
sudo cp /etc/nginx/sites-available/asterdex-api.backup.YYYYMMDD_HHMMSS \
  /etc/nginx/sites-available/asterdex-api
sudo nginx -t
sudo systemctl reload nginx
```

## Future Enhancements

Possible improvements:
- [ ] Add SSL/HTTPS configuration to welcome page
- [ ] Add real-time status indicator (check /health endpoint)
- [ ] Add usage statistics or metrics
- [ ] Add authentication for sensitive endpoints
- [ ] Add rate limiting configuration
- [ ] Add monitoring/alerting setup

## Questions?

See documentation:
- [QUICK_UPDATE.md](QUICK_UPDATE.md) - How to update
- [README.md](README.md) - Overview
- [NGINX_TROUBLESHOOTING.md](../NGINX_TROUBLESHOOTING.md) - Nginx issues
- [DIGITALOCEAN_DEPLOYMENT.md](../DIGITALOCEAN_DEPLOYMENT.md) - Full deployment guide
