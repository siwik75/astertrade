# Nginx Reverse Proxy Explained

## TL;DR

**For DigitalOcean App Platform: You DON'T need Nginx!** It's built-in.

**For DigitalOcean Droplet (VPS): You DO need Nginx** for SSL and production features.

## What is a Reverse Proxy?

### Simple Explanation

A reverse proxy sits between the internet and your application, forwarding requests and adding features.

```
Internet → Nginx (Reverse Proxy) → Your FastAPI App
```

**Think of it as:** A receptionist at a company
- Visitors talk to the receptionist (Nginx)
- Receptionist forwards them to the right person (your app)
- Receptionist can also handle security, directions, etc.

### Technical Explanation

```
┌─────────────┐
│   Internet  │
│   (Port 80) │
│  (Port 443) │
└──────┬──────┘
       │ HTTP/HTTPS
       ↓
┌──────────────────────────────────────┐
│         Nginx (Reverse Proxy)        │
│                                      │
│  • Receives requests on port 80/443 │
│  • Handles SSL/TLS (HTTPS)          │
│  • Forwards to your app             │
│  • Returns response to client       │
└──────┬───────────────────────────────┘
       │ HTTP (internal)
       ↓
┌──────────────────────────────────────┐
│      Your FastAPI App                │
│      (Port 8000, localhost)          │
│                                      │
│  • Receives from Nginx only         │
│  • Not exposed to internet          │
│  • Processes requests               │
└──────────────────────────────────────┘
```

---

## Why Use Nginx?

### 1. SSL/HTTPS Termination

**Without Nginx:**
```
Internet → Your App (port 8000)
❌ HTTP only (not secure)
❌ No encryption
❌ Browsers show "Not Secure"
```

**With Nginx:**
```
Internet → Nginx (port 443, HTTPS) → Your App (port 8000, HTTP)
✅ HTTPS to internet
✅ SSL certificate handled by Nginx
✅ Browsers show "Secure"
```

**Why this matters:**
- TradingView requires HTTPS for webhooks
- Protects your API credentials in transit
- Professional and secure

### 2. Port Management

**Without Nginx:**
```
Your app runs on port 8000
Users access: http://your-ip:8000
❌ Looks unprofessional
❌ Firewall issues
❌ Port must be exposed
```

**With Nginx:**
```
Nginx runs on port 80 (HTTP) and 443 (HTTPS)
Your app runs on port 8000 (internal only)
Users access: https://your-domain.com
✅ Standard ports
✅ Professional URLs
✅ App not directly exposed
```

### 3. Security Layer

**Nginx provides:**
- ✅ Rate limiting (prevent abuse)
- ✅ Request filtering (block malicious requests)
- ✅ IP whitelisting/blacklisting
- ✅ DDoS protection (basic)
- ✅ Hide your app's technology stack

### 4. Performance

**Nginx is optimized for:**
- ✅ Serving static files (faster than Python)
- ✅ Handling many concurrent connections
- ✅ Compression (gzip)
- ✅ Caching (if needed)
- ✅ Load balancing (multiple app instances)

### 5. Multiple Services

**With Nginx, you can run multiple apps:**
```
https://your-domain.com/api → Your trading API (port 8000)
https://your-domain.com/dashboard → Web dashboard (port 3000)
https://your-domain.com/docs → Documentation (port 8080)
```

All on one server, one domain!

---

## When Do You Need Nginx?

### ✅ You NEED Nginx if:

1. **Deploying on a Droplet/VPS**
   - You're managing your own server
   - You need SSL/HTTPS
   - You want professional URLs

2. **Running Multiple Services**
   - Multiple apps on one server
   - Different ports for different services

3. **Need Advanced Features**
   - Rate limiting
   - IP whitelisting
   - Custom routing rules
   - Load balancing

4. **Production Environment**
   - Professional deployment
   - Security requirements
   - Performance optimization

### ❌ You DON'T Need Nginx if:

1. **Using DigitalOcean App Platform**
   - Built-in reverse proxy ✓
   - Automatic SSL ✓
   - Load balancing ✓
   - Professional URLs ✓

2. **Using Heroku/Railway/Render**
   - These platforms handle it for you

3. **Local Development**
   - Just run your app directly
   - No need for complexity

4. **Using Cloud Run/Lambda**
   - Serverless platforms handle routing

---

## How to Use Nginx (Droplet Deployment)

### Step 1: Install Nginx

```bash
# SSH into your Droplet
ssh root@YOUR_DROPLET_IP

# Update system
apt-get update

# Install Nginx
apt-get install nginx -y

# Verify installation
nginx -v
```

### Step 2: Configure Nginx

Create configuration file:

```bash
nano /etc/nginx/sites-available/asterdex-api
```

Paste this configuration:

```nginx
# /etc/nginx/sites-available/asterdex-api

server {
    # Listen on port 80 (HTTP)
    listen 80;
    listen [::]:80;
    
    # Your domain name
    server_name api.yourdomain.com;
    
    # Redirect HTTP to HTTPS (after SSL is set up)
    # return 301 https://$server_name$request_uri;
    
    # Proxy settings
    location / {
        # Forward to your FastAPI app
        proxy_pass http://127.0.0.1:8000;
        
        # Preserve original request information
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Health check endpoint (optional)
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

### Step 3: Enable Configuration

```bash
# Create symbolic link to enable site
ln -s /etc/nginx/sites-available/asterdex-api /etc/nginx/sites-enabled/

# Test configuration
nginx -t

# If test passes, reload Nginx
systemctl reload nginx

# Enable Nginx to start on boot
systemctl enable nginx
```

### Step 4: Set Up SSL with Let's Encrypt

```bash
# Install Certbot
apt-get install certbot python3-certbot-nginx -y

# Get SSL certificate (replace with your domain)
certbot --nginx -d api.yourdomain.com

# Follow prompts:
# - Enter email address
# - Agree to terms
# - Choose to redirect HTTP to HTTPS (recommended)

# Certbot automatically updates Nginx config!
```

After SSL setup, your Nginx config will look like:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL certificates (added by Certbot)
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Step 5: Test

```bash
# Check Nginx status
systemctl status nginx

# Test your API
curl https://api.yourdomain.com/health

# Should return: {"status": "healthy", ...}
```

---

## Advanced Nginx Features

### Rate Limiting

Protect against abuse:

```nginx
# Define rate limit zone (10 requests per second)
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    location / {
        # Apply rate limit
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        # ... other settings
    }
}
```

### IP Whitelisting

Only allow specific IPs:

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    location / {
        # Allow specific IPs
        allow 1.2.3.4;        # Your IP
        allow 5.6.7.8;        # TradingView IP
        deny all;             # Deny everyone else
        
        proxy_pass http://127.0.0.1:8000;
        # ... other settings
    }
}
```

### Custom Headers

Add security headers:

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        # ... other settings
    }
}
```

### Logging

Custom access logs:

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # Custom log format
    access_log /var/log/nginx/asterdex-api-access.log;
    error_log /var/log/nginx/asterdex-api-error.log;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        # ... other settings
    }
}
```

### Load Balancing

Run multiple app instances:

```nginx
# Define upstream servers
upstream asterdex_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    location / {
        # Load balance across instances
        proxy_pass http://asterdex_backend;
        # ... other settings
    }
}
```

---

## Nginx vs App Platform

### DigitalOcean App Platform (No Nginx Needed)

```
Internet
    ↓
DigitalOcean Edge Network (DDoS protection)
    ↓
Load Balancer (automatic SSL, routing)
    ↓
Your App Container
```

**Built-in features:**
- ✅ Automatic SSL
- ✅ Load balancing
- ✅ DDoS protection
- ✅ Professional URLs
- ✅ Zero configuration

**You get all Nginx benefits without managing it!**

### Droplet with Nginx (Manual Setup)

```
Internet
    ↓
Nginx (you configure SSL, routing, security)
    ↓
Your App (Docker container)
```

**You manage:**
- ⚙️ Nginx configuration
- ⚙️ SSL certificates (Certbot)
- ⚙️ Security rules
- ⚙️ Updates and maintenance

**More control, more responsibility.**

---

## Common Nginx Commands

```bash
# Test configuration
nginx -t

# Reload configuration (no downtime)
systemctl reload nginx

# Restart Nginx
systemctl restart nginx

# Stop Nginx
systemctl stop nginx

# Start Nginx
systemctl start nginx

# Check status
systemctl status nginx

# View error logs
tail -f /var/log/nginx/error.log

# View access logs
tail -f /var/log/nginx/access.log

# Renew SSL certificate
certbot renew --dry-run
```

---

## Troubleshooting

### Issue: "502 Bad Gateway"

**Cause:** Nginx can't connect to your app

**Solutions:**
```bash
# Check if your app is running
docker compose ps

# Check app logs
docker compose logs asterdex-api

# Verify app is listening on port 8000
curl http://localhost:8000/health

# Check Nginx error logs
tail -f /var/log/nginx/error.log
```

### Issue: "Connection refused"

**Cause:** App not running or wrong port

**Solutions:**
```bash
# Start your app
docker compose up -d

# Verify port in Nginx config matches app port
# Nginx: proxy_pass http://127.0.0.1:8000
# App: Should be running on port 8000
```

### Issue: SSL certificate errors

**Cause:** Certificate expired or not properly configured

**Solutions:**
```bash
# Check certificate status
certbot certificates

# Renew certificate
certbot renew

# Test renewal
certbot renew --dry-run
```

### Issue: "Permission denied"

**Cause:** Nginx can't access files or ports

**Solutions:**
```bash
# Check Nginx user
ps aux | grep nginx

# Fix permissions
chown -R www-data:www-data /var/www

# Check SELinux (if applicable)
getenforce
```

---

## Decision Matrix

### Should I Use Nginx?

```
Are you using DigitalOcean App Platform?
    │
    ├─ YES → Don't use Nginx (built-in) ✓
    │
    └─ NO → Are you using a Droplet/VPS?
            │
            ├─ YES → Use Nginx ✓
            │
            └─ NO → Are you using Heroku/Railway/Render?
                    │
                    ├─ YES → Don't use Nginx (built-in) ✓
                    │
                    └─ NO → Are you deploying locally?
                            │
                            ├─ YES → Don't use Nginx (not needed) ✓
                            │
                            └─ NO → Use Nginx for production ✓
```

---

## Summary

### What is Nginx?

A reverse proxy that sits between the internet and your app, providing:
- SSL/HTTPS termination
- Professional URLs (port 80/443)
- Security features
- Performance optimization
- Load balancing

### When to Use Nginx?

**Use Nginx:**
- ✅ Droplet/VPS deployment
- ✅ Need SSL/HTTPS
- ✅ Production environment
- ✅ Multiple services on one server
- ✅ Advanced security/performance needs

**Don't Use Nginx:**
- ❌ DigitalOcean App Platform (built-in)
- ❌ Heroku/Railway/Render (built-in)
- ❌ Local development (not needed)
- ❌ Serverless platforms (handled for you)

### Quick Setup

```bash
# Install
apt-get install nginx certbot python3-certbot-nginx

# Configure
nano /etc/nginx/sites-available/asterdex-api
ln -s /etc/nginx/sites-available/asterdex-api /etc/nginx/sites-enabled/

# Enable SSL
certbot --nginx -d api.yourdomain.com

# Test
curl https://api.yourdomain.com/health
```

### For Your Project

**If using App Platform:** You're all set! No Nginx needed.

**If using Droplet:** Follow the setup guide in `DIGITALOCEAN_DEPLOYMENT.md` - Nginx is included in the automated setup script.

---

**Bottom line:** Nginx is a powerful tool for Droplet deployments, but if you're using App Platform, it's already handled for you! 🚀
