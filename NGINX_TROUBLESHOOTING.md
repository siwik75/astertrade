# Nginx HTTPS Troubleshooting Guide

## Quick Diagnostics

Run these commands on your Droplet to diagnose the issue:

```bash
# 1. Check if Nginx is running
systemctl status nginx

# 2. Check if your app is accessible locally
curl http://localhost:8000/health

# 3. Check Nginx configuration
nginx -t

# 4. Check if port 443 is listening
sudo netstat -tlnp | grep :443

# 5. Check SSL certificate status
sudo certbot certificates

# 6. View Nginx error logs
sudo tail -50 /var/log/nginx/error.log

# 7. View Nginx access logs
sudo tail -50 /var/log/nginx/access.log
```

## Common Issues and Solutions

### Issue 1: SSL Certificate Not Installed

**Symptoms:**
- `curl https://your-domain.com` fails
- Browser shows "Connection refused" or "SSL error"
- Port 443 not listening

**Solution:**

```bash
# Install Certbot if not already installed
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx -y

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com

# Follow the prompts:
# - Enter email address
# - Agree to terms of service
# - Choose to redirect HTTP to HTTPS (option 2)
```

### Issue 2: Nginx Not Configured Correctly

**Check your Nginx configuration:**

```bash
# View your Nginx config
sudo cat /etc/nginx/sites-available/asterdex-api

# Or edit it
sudo nano /etc/nginx/sites-available/asterdex-api
```

**Correct configuration should look like this:**

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS (after SSL is set up)
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com;
    
    # SSL certificates (added by Certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    # Proxy settings
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

**Apply the configuration:**

```bash
# Test configuration
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx
```

### Issue 3: Domain Not Pointing to Droplet

**Check DNS:**

```bash
# Check if domain resolves to your Droplet IP
dig your-domain.com +short

# Or use nslookup
nslookup your-domain.com

# Should return your Droplet's IP address
```

**If DNS is wrong:**
1. Go to your domain registrar (Namecheap, GoDaddy, etc.)
2. Add/Update A record:
   - Type: A
   - Name: @ (or your subdomain)
   - Value: YOUR_DROPLET_IP
   - TTL: 300 (or automatic)
3. Wait 5-15 minutes for DNS propagation

### Issue 4: Firewall Blocking Port 443

**Check firewall:**

```bash
# Check UFW status
sudo ufw status

# If UFW is active, ensure ports are allowed
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw reload
```

**Check iptables:**

```bash
# List iptables rules
sudo iptables -L -n

# If port 443 is blocked, allow it
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

### Issue 5: Nginx Not Enabled or Running

**Fix Nginx service:**

```bash
# Enable Nginx to start on boot
sudo systemctl enable nginx

# Start Nginx
sudo systemctl start nginx

# Check status
sudo systemctl status nginx

# If failed, check error logs
sudo journalctl -u nginx -n 50
```

### Issue 6: Port 8000 Not Accessible

**Check if your app is running:**

```bash
# Check Docker container
docker compose ps

# Should show "Up" status
# If not, start it
docker compose up -d

# Test app directly
curl http://localhost:8000/health

# Should return: {"status":"healthy",...}
```

### Issue 7: SELinux Blocking Nginx

**If on CentOS/RHEL:**

```bash
# Check SELinux status
getenforce

# If Enforcing, allow Nginx to connect
sudo setsebool -P httpd_can_network_connect 1
```

## Step-by-Step Setup (If Starting Fresh)

### 1. Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/asterdex-api
```

Paste this (replace `your-domain.com` with your actual domain):

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Enable the Site

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/asterdex-api /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 3. Test HTTP First

```bash
# Test locally
curl http://localhost/health

# Test from outside (replace with your domain)
curl http://your-domain.com/health

# Should return: {"status":"healthy",...}
```

### 4. Add SSL Certificate

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx -y

# Get certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com

# Certbot will:
# 1. Verify domain ownership
# 2. Get SSL certificate
# 3. Update Nginx config automatically
# 4. Set up auto-renewal

# Choose option 2 to redirect HTTP to HTTPS
```

### 5. Test HTTPS

```bash
# Test locally
curl https://your-domain.com/health

# Should return: {"status":"healthy",...}

# Test in browser
# Visit: https://your-domain.com/docs
```

## Verification Checklist

Run through this checklist:

```bash
# 1. App is running
docker compose ps
# Status should be "Up"

# 2. App responds locally
curl http://localhost:8000/health
# Should return JSON

# 3. Nginx is running
systemctl status nginx
# Should be "active (running)"

# 4. Nginx config is valid
sudo nginx -t
# Should say "syntax is ok" and "test is successful"

# 5. Port 80 is listening
sudo netstat -tlnp | grep :80
# Should show nginx

# 6. Port 443 is listening (after SSL)
sudo netstat -tlnp | grep :443
# Should show nginx

# 7. SSL certificate exists
sudo certbot certificates
# Should show your domain with valid certificate

# 8. Domain resolves correctly
dig your-domain.com +short
# Should return your Droplet IP

# 9. HTTP works
curl http://your-domain.com/health
# Should return JSON or redirect to HTTPS

# 10. HTTPS works
curl https://your-domain.com/health
# Should return JSON
```

## Common Error Messages

### "502 Bad Gateway"

**Cause:** Nginx can't connect to your app

**Fix:**
```bash
# Check if app is running
docker compose ps

# Check app logs
docker compose logs asterdex-api

# Restart app
docker compose restart

# Check Nginx error log
sudo tail -f /var/log/nginx/error.log
```

### "Connection refused"

**Cause:** Nginx not running or port blocked

**Fix:**
```bash
# Start Nginx
sudo systemctl start nginx

# Check firewall
sudo ufw status
sudo ufw allow 'Nginx Full'
```

### "SSL certificate problem"

**Cause:** Certificate not installed or expired

**Fix:**
```bash
# Check certificate
sudo certbot certificates

# Renew certificate
sudo certbot renew

# If certificate doesn't exist, get one
sudo certbot --nginx -d your-domain.com
```

### "Name or service not known"

**Cause:** Domain doesn't resolve to your server

**Fix:**
1. Check DNS settings at your domain registrar
2. Add A record pointing to your Droplet IP
3. Wait for DNS propagation (5-15 minutes)

## Testing from Different Locations

### Test from Droplet (local)

```bash
# Test app directly
curl http://localhost:8000/health

# Test through Nginx (HTTP)
curl http://localhost/health

# Test through Nginx (HTTPS)
curl https://your-domain.com/health
```

### Test from Your Computer

```bash
# Test HTTP
curl http://your-domain.com/health

# Test HTTPS
curl https://your-domain.com/health

# Test with verbose output
curl -v https://your-domain.com/health
```

### Test in Browser

1. Visit: `https://your-domain.com/health`
2. Should see: `{"status":"healthy",...}`
3. Check SSL certificate (click padlock icon)
4. Visit: `https://your-domain.com/docs`
5. Should see: Interactive API documentation

## Quick Fix Commands

```bash
# Restart everything
sudo systemctl restart nginx
docker compose restart

# View all logs
sudo tail -f /var/log/nginx/error.log &
docker compose logs -f

# Force SSL certificate renewal
sudo certbot renew --force-renewal

# Reset Nginx configuration
sudo rm /etc/nginx/sites-enabled/asterdex-api
sudo ln -s /etc/nginx/sites-available/asterdex-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Get Help

If still having issues, gather this information:

```bash
# 1. Nginx status
systemctl status nginx

# 2. Nginx config test
sudo nginx -t

# 3. SSL certificate status
sudo certbot certificates

# 4. DNS resolution
dig your-domain.com +short

# 5. Port status
sudo netstat -tlnp | grep -E ':(80|443|8000)'

# 6. Recent Nginx errors
sudo tail -50 /var/log/nginx/error.log

# 7. App status
docker compose ps
docker compose logs --tail=50 asterdex-api

# 8. Test from Droplet
curl -v http://localhost:8000/health
curl -v http://localhost/health
curl -v https://your-domain.com/health
```

Share this output for troubleshooting assistance.
