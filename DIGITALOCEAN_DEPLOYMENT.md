# DigitalOcean Deployment Guide

## Recommended: App Platform Deployment

This is the easiest and most cost-effective way to deploy your AsterDEX Trading API.

### Prerequisites

1. DigitalOcean account ([Sign up here](https://www.digitalocean.com))
2. Your code in a Git repository (GitHub, GitLab, or Bitbucket)
3. Your AsterDEX API credentials ready

### Step 1: Push Your Code to Git

If you haven't already, push your code to GitHub:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Step 2: Create App on DigitalOcean

1. **Log in to DigitalOcean** and go to [App Platform](https://cloud.digitalocean.com/apps)

2. **Click "Create App"**

3. **Connect Your Repository**
   - Choose your Git provider (GitHub/GitLab/Bitbucket)
   - Authorize DigitalOcean to access your repositories
   - Select your repository
   - Select the branch (usually `main` or `master`)
   - Enable "Autodeploy" to automatically deploy on git push

4. **Configure Your App**
   - DigitalOcean will auto-detect your Dockerfile
   - **Resource Type**: Web Service
   - **HTTP Port**: 8000
   - **HTTP Request Routes**: /

5. **Choose Your Plan**
   - **Basic Plan - $5/month**: 512 MB RAM, 1 vCPU (good for testing)
   - **Basic Plan - $12/month**: 1 GB RAM, 1 vCPU (recommended for production)
   - **Professional Plans**: For higher traffic

6. **Set Environment Variables**
   
   Click "Edit" next to your app component, then go to "Environment Variables":
   
   **Required Variables:**
   ```
   ASTERDEX_USER_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   ASTERDEX_SIGNER_ADDRESS=0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199
   ASTERDEX_PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
   ```
   
   **Optional Variables (with defaults):**
   ```
   ASTERDEX_BASE_URL=https://fapi.asterdex.com
   SERVER_HOST=0.0.0.0
   SERVER_PORT=8000
   WEBHOOK_SECRET=your-secret-token-here
   DEFAULT_LEVERAGE=10
   DEFAULT_MARGIN_TYPE=CROSSED
   REQUEST_TIMEOUT=30
   MAX_RETRIES=3
   RATE_LIMIT_RETRY_DELAY=2
   LOG_LEVEL=INFO
   ```
   
   **Important**: Mark `ASTERDEX_PRIVATE_KEY` as "Encrypted" for security!

7. **Configure Health Checks** (Optional but recommended)
   - Path: `/health`
   - Port: 8000
   - Initial delay: 5 seconds
   - Period: 30 seconds

8. **Review and Create**
   - Review your configuration
   - Click "Create Resources"
   - Wait 3-5 minutes for deployment

### Step 3: Verify Deployment

Once deployed, DigitalOcean will provide you with a URL like:
```
https://your-app-name-xxxxx.ondigitalocean.app
```

Test your deployment:

```bash
# Health check
curl https://your-app-name-xxxxx.ondigitalocean.app/health

# API documentation
# Visit in browser: https://your-app-name-xxxxx.ondigitalocean.app/docs
```

### Step 4: Configure TradingView Webhook

In TradingView, set your webhook URL to:
```
https://your-app-name-xxxxx.ondigitalocean.app/webhook/tradingview
```

If you set `WEBHOOK_SECRET`, add it as a custom header:
- Header Name: `X-Webhook-Secret`
- Header Value: `your-secret-token-here`

### Step 5: Set Up Custom Domain (Optional)

1. Go to your App settings in DigitalOcean
2. Click "Domains" tab
3. Add your custom domain (e.g., `api.yourdomain.com`)
4. Update your DNS records as instructed
5. SSL certificate is automatically provisioned

---

## Alternative: Droplet Deployment (VPS)

If you prefer more control, you can deploy on a Droplet (VPS).

### Step 1: Create a Droplet

1. Go to [DigitalOcean Droplets](https://cloud.digitalocean.com/droplets)
2. Click "Create Droplet"
3. Choose:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic ($6/month - 1GB RAM, 1 vCPU)
   - **Datacenter**: Choose closest to you or your users
   - **Authentication**: SSH key (recommended) or password
4. Click "Create Droplet"

### Step 2: Connect to Your Droplet

```bash
ssh root@YOUR_DROPLET_IP
```

### Step 3: Install Docker

```bash
# Update system
apt-get update
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt-get install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

### Step 4: Deploy Your Application

```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# Create .env file
nano .env
```

Paste your environment variables:
```bash
ASTERDEX_USER_ADDRESS=0xYOUR_ADDRESS
ASTERDEX_SIGNER_ADDRESS=0xYOUR_SIGNER
ASTERDEX_PRIVATE_KEY=0xYOUR_KEY
WEBHOOK_SECRET=your-secret-here
LOG_LEVEL=INFO
```

Save and exit (Ctrl+X, Y, Enter)

```bash
# Start the application
docker compose up -d

# Check status
docker compose ps
docker compose logs -f
```

### Step 5: Set Up Nginx Reverse Proxy

```bash
# Install Nginx
apt-get install nginx -y

# Create Nginx configuration
nano /etc/nginx/sites-available/asterdex-api
```

Paste this configuration:
```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;
    }
}
```

Enable the site:
```bash
ln -s /etc/nginx/sites-available/asterdex-api /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Step 6: Set Up SSL with Let's Encrypt

```bash
# Install Certbot
apt-get install certbot python3-certbot-nginx -y

# Get SSL certificate (replace with your domain)
certbot --nginx -d api.yourdomain.com

# Test auto-renewal
certbot renew --dry-run
```

### Step 7: Set Up Firewall

```bash
# Configure UFW firewall
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable
ufw status
```

---

## Cost Comparison

| Option | Monthly Cost | Pros | Cons |
|--------|-------------|------|------|
| **App Platform (Basic)** | $5-12 | Fully managed, auto-scaling, SSL included, easy updates | Less control |
| **Droplet + Docker** | $6+ | Full control, can run multiple services | Manual maintenance, security updates |
| **Kubernetes** | $12+ | Enterprise-grade, highly scalable | Complex, overkill for single service |

---

## Monitoring and Maintenance

### App Platform

- **View Logs**: Go to your app → Runtime Logs
- **Metrics**: Built-in CPU, memory, and request metrics
- **Alerts**: Set up alerts for downtime or errors
- **Updates**: Just push to Git, auto-deploys

### Droplet

```bash
# View logs
docker compose logs -f asterdex-api

# Restart service
docker compose restart

# Update application
git pull
docker compose down
docker compose build
docker compose up -d

# Monitor resources
docker stats
```

---

## Security Checklist

- [ ] Set strong `WEBHOOK_SECRET`
- [ ] Mark `ASTERDEX_PRIVATE_KEY` as encrypted/secret
- [ ] Enable HTTPS (automatic on App Platform)
- [ ] Set `LOG_LEVEL=INFO` or `WARNING` in production
- [ ] Enable firewall (if using Droplet)
- [ ] Regularly update dependencies
- [ ] Monitor logs for suspicious activity
- [ ] Set up uptime monitoring (UptimeRobot, Pingdom, etc.)

---

## Troubleshooting

### App Platform Issues

**Build fails:**
- Check build logs in DigitalOcean dashboard
- Verify Dockerfile syntax
- Ensure all dependencies are in requirements.txt

**App crashes:**
- Check Runtime Logs
- Verify environment variables are set correctly
- Check health endpoint: `/health`

**Webhook not working:**
- Verify URL is publicly accessible
- Check webhook secret matches
- Review logs for incoming requests

### Droplet Issues

**Can't connect to Droplet:**
```bash
# Check if service is running
docker compose ps

# Check logs
docker compose logs asterdex-api

# Restart service
docker compose restart
```

**Out of memory:**
```bash
# Check memory usage
free -h

# Upgrade Droplet or optimize application
```

---

## Next Steps

1. Deploy using App Platform (recommended)
2. Test health endpoint and API docs
3. Configure TradingView webhook
4. Set up monitoring and alerts
5. Test with small trades first
6. Monitor logs and performance

Need help? Check the main [README.md](README.md) for more details.
