# Apply Changes to Your Droplet Right Now

## One-Line Command

SSH into your droplet and run:

```bash
cd /opt/asterdex-trading-api && git pull && bash .digitalocean/update-nginx-welcome.sh
```

That's it! This will:
1. Pull the latest changes from your repository
2. Create the welcome page
3. Update nginx configuration
4. Reload nginx

## Step-by-Step (If You Prefer)

```bash
# 1. SSH into your droplet
ssh root@46.101.196.30

# 2. Navigate to your app directory
cd /opt/asterdex-trading-api

# 3. Pull latest changes
git pull

# 4. Run the update script
bash .digitalocean/update-nginx-welcome.sh
```

## What You'll See

The script will:
- Ask for your domain name (enter `astertrade.ai`)
- Copy welcome page from `.digitalocean/welcome.html` to `/var/www/asterdex/index.html`
- Update nginx configuration
- Test the configuration
- Reload nginx

## Verify It Worked

After running, test in your browser:
- Visit: `http://astertrade.ai/` → Should show welcome page
- Visit: `http://46.101.196.30/` → Should show welcome page
- Visit: `http://astertrade.ai/docs` → Should show API docs
- Visit: `http://astertrade.ai/health` → Should show health status

Or test with curl:

```bash
# From your local machine
curl http://astertrade.ai/
curl http://46.101.196.30/
curl http://astertrade.ai/health
```

## If Something Goes Wrong

The script creates backups automatically. To rollback:

```bash
# List backups
ls -la /etc/nginx/sites-available/asterdex-api.backup.*

# Restore latest backup
LATEST=$(ls -t /etc/nginx/sites-available/asterdex-api.backup.* | head -1)
sudo cp "$LATEST" /etc/nginx/sites-available/asterdex-api
sudo nginx -t
sudo systemctl reload nginx
```

## Need Help?

Check [QUICK_UPDATE.md](QUICK_UPDATE.md) for detailed troubleshooting.
