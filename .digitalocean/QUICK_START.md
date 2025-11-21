# DigitalOcean Quick Start Guide

## 🎯 Recommended: App Platform (5 minutes)

**Best for:** Easy deployment, automatic scaling, no server management

### Steps:

1. **Push code to GitHub**
   ```bash
   git push origin main
   ```

2. **Go to DigitalOcean**
   - Visit: https://cloud.digitalocean.com/apps
   - Click "Create App"
   - Connect your GitHub repository

3. **Configure**
   - Auto-detected: Dockerfile ✓
   - Port: 8000
   - Plan: $5/month (Basic) or $12/month (Recommended)

4. **Add Environment Variables**
   ```
   ASTERDEX_USER_ADDRESS=0xYOUR_ADDRESS
   ASTERDEX_SIGNER_ADDRESS=0xYOUR_SIGNER
   ASTERDEX_PRIVATE_KEY=0xYOUR_KEY (mark as encrypted!)
   WEBHOOK_SECRET=your-secret-here
   ```

5. **Deploy**
   - Click "Create Resources"
   - Wait 3-5 minutes
   - Get your URL: `https://your-app-xxxxx.ondigitalocean.app`

6. **Test**
   ```bash
   curl https://your-app-xxxxx.ondigitalocean.app/health
   ```

7. **Configure TradingView**
   - Webhook URL: `https://your-app-xxxxx.ondigitalocean.app/webhook/tradingview`
   - Add header: `X-Webhook-Secret: your-secret-here`

**Done! 🎉**

---

## 🔧 Alternative: Droplet (15 minutes)

**Best for:** Full control, custom configurations

### Steps:

1. **Create Droplet**
   - Go to: https://cloud.digitalocean.com/droplets
   - Ubuntu 22.04 LTS
   - $6/month (1GB RAM)
   - Add SSH key

2. **Connect**
   ```bash
   ssh root@YOUR_DROPLET_IP
   ```

3. **Run Setup Script**
   ```bash
   curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/.digitalocean/droplet-setup.sh | bash
   ```
   
   Or manually:
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com | sh
   apt-get install docker-compose-plugin -y
   
   # Clone and deploy
   git clone YOUR_REPO_URL /opt/asterdex-trading-api
   cd /opt/asterdex-trading-api
   cp .env.example .env
   nano .env  # Add your credentials
   docker compose up -d
   ```

4. **Set up Nginx + SSL** (optional)
   ```bash
   apt-get install nginx certbot python3-certbot-nginx -y
   # Configure Nginx (see full guide)
   certbot --nginx -d yourdomain.com
   ```

**Done! 🎉**

---

## 📊 Comparison

| Feature | App Platform | Droplet |
|---------|-------------|---------|
| **Setup Time** | 5 minutes | 15 minutes |
| **Cost** | $5-12/month | $6+/month |
| **Maintenance** | None | Manual |
| **SSL** | Automatic | Manual |
| **Scaling** | Automatic | Manual |
| **Control** | Limited | Full |
| **Best For** | Most users | Advanced users |

---

## 🔍 What to Choose?

### Choose App Platform if:
- ✅ You want the easiest deployment
- ✅ You don't want to manage servers
- ✅ You want automatic SSL and scaling
- ✅ You're okay with less control

### Choose Droplet if:
- ✅ You need full server control
- ✅ You want to run multiple services
- ✅ You're comfortable with Linux administration
- ✅ You need custom configurations

---

## 🆘 Need Help?

- Full guide: [DIGITALOCEAN_DEPLOYMENT.md](DIGITALOCEAN_DEPLOYMENT.md)
- Main docs: [README.md](../README.md)
- DigitalOcean docs: https://docs.digitalocean.com

---

## ✅ Post-Deployment Checklist

- [ ] Health check works: `/health`
- [ ] API docs accessible: `/docs`
- [ ] Environment variables set correctly
- [ ] TradingView webhook configured
- [ ] SSL/HTTPS enabled
- [ ] Monitoring set up
- [ ] Test with small trade first!
