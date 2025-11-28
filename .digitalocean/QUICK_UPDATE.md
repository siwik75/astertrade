# Quick Update Guide

## Update Your Existing Droplet

If you already have a droplet running and want to apply the new nginx configuration and welcome page:

### Option 1: Quick Update Script (Recommended)

```bash
# SSH into your droplet
ssh root@46.101.196.30

# Navigate to your app directory
cd /opt/asterdex-trading-api

# Pull latest changes
git pull

# Run the update script
bash .digitalocean/update-nginx-welcome.sh
```

This will:
- ✅ Create the welcome page at `/var/www/asterdex/index.html`
- ✅ Update nginx configuration to serve welcome page at root
- ✅ Keep all API endpoints working (`/docs`, `/health`, `/webhook`)
- ✅ Make both domain and IP show the same content
- ✅ Backup your old config before updating

### Option 2: Re-run Full Setup (Idempotent)

```bash
# SSH into your droplet
ssh root@46.101.196.30

# Navigate to your app directory
cd /opt/asterdex-trading-api

# Pull latest changes
git pull

# Re-run setup (safe - won't overwrite .env or reinstall packages)
bash .digitalocean/droplet-setup.sh
```

The setup script is now idempotent, meaning:
- ✅ Won't reinstall Docker if already installed
- ✅ Won't overwrite your `.env` file
- ✅ Will update nginx config to latest version
- ✅ Will update welcome page to latest version
- ✅ Safe to run multiple times

### Option 3: Manual Update

If you prefer to do it manually:

```bash
# SSH into your droplet
ssh root@46.101.196.30

# Create welcome page directory
sudo mkdir -p /var/www/asterdex

# Create welcome page (copy content from .digitalocean/welcome.html)
sudo nano /var/www/asterdex/index.html
# Paste the HTML content

# Update nginx config (copy content from .digitalocean/nginx.conf)
sudo nano /etc/nginx/sites-available/asterdex-api
# Update the configuration

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

## What Changes

### Before Update
- `astertrade.ai` → Nginx default page
- `46.101.196.30` → FastAPI docs

### After Update
- `astertrade.ai` → Beautiful welcome page
- `46.101.196.30` → Beautiful welcome page
- `astertrade.ai/docs` → FastAPI docs
- `astertrade.ai/health` → Health check
- `astertrade.ai/webhook/tradingview` → Webhook (still works!)

## Verify Update

After running the update, test:

```bash
# Test welcome page
curl http://46.101.196.30/

# Test API docs
curl http://46.101.196.30/docs

# Test health check
curl http://46.101.196.30/health

# Test with domain
curl http://astertrade.ai/
curl http://astertrade.ai/health
```

## Rollback

If something goes wrong, the update script creates backups:

```bash
# List backups
ls -la /etc/nginx/sites-available/asterdex-api.backup.*

# Restore from backup
sudo cp /etc/nginx/sites-available/asterdex-api.backup.YYYYMMDD_HHMMSS /etc/nginx/sites-available/asterdex-api
sudo nginx -t
sudo systemctl reload nginx
```

## Troubleshooting

### Nginx test fails
```bash
# Check syntax errors
sudo nginx -t

# View error log
sudo tail -50 /var/log/nginx/error.log
```

### Welcome page not showing
```bash
# Check if file exists
ls -la /var/www/asterdex/index.html

# Check nginx config
sudo cat /etc/nginx/sites-available/asterdex-api | grep "location = /"

# Check nginx is running
sudo systemctl status nginx
```

### API endpoints not working
```bash
# Check if app is running
cd /opt/asterdex-trading-api
docker compose ps

# Check app logs
docker compose logs -f

# Test app directly
curl http://localhost:8000/health
```

## Need Help?

Check the full documentation:
- [NGINX_TROUBLESHOOTING.md](../NGINX_TROUBLESHOOTING.md)
- [DROPLET_TROUBLESHOOTING.md](../DROPLET_TROUBLESHOOTING.md)
- [DIGITALOCEAN_DEPLOYMENT.md](../DIGITALOCEAN_DEPLOYMENT.md)
