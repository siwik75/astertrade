#!/bin/bash
# DigitalOcean Droplet Setup Script
# Run this on a fresh Ubuntu 22.04 Droplet or to update existing setup
# This script is idempotent - safe to run multiple times

set -e

echo "🚀 Setting up AsterDEX Trading API on DigitalOcean Droplet..."

# Update system
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# Install Docker (idempotent)
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose (idempotent)
if ! docker compose version &> /dev/null; then
    echo "🔧 Installing Docker Compose..."
    apt-get install docker-compose-plugin -y
else
    echo "✅ Docker Compose already installed"
fi

# Verify installations
echo "✅ Verifying installations..."
docker --version
docker compose version

# Install Nginx (idempotent)
if ! command -v nginx &> /dev/null; then
    echo "🌐 Installing Nginx..."
    apt-get install nginx -y
else
    echo "✅ Nginx already installed"
fi

# Install Certbot for SSL (idempotent)
if ! command -v certbot &> /dev/null; then
    echo "🔒 Installing Certbot..."
    apt-get install certbot python3-certbot-nginx -y
else
    echo "✅ Certbot already installed"
fi

# Create application directory
echo "📁 Setting up application directory..."
mkdir -p /opt/asterdex-trading-api
cd /opt/asterdex-trading-api

# Clone or update repository (idempotent)
if [ ! -d ".git" ]; then
    # Prompt for repository URL
    echo ""
    echo "📥 Please enter your Git repository URL:"
    read -p "Repository URL: " REPO_URL

    if [ -z "$REPO_URL" ]; then
        echo "❌ Repository URL is required!"
        exit 1
    fi

    echo "📥 Cloning repository..."
    git clone "$REPO_URL" .
else
    echo "✅ Repository already exists, pulling latest changes..."
    git pull
fi

# Create .env file (idempotent - only if doesn't exist)
if [ ! -f ".env" ]; then
    echo ""
    echo "⚙️  Creating .env file..."
    echo "Please provide your AsterDEX credentials:"
    read -p "ASTERDEX_USER_ADDRESS: " USER_ADDRESS
    read -p "ASTERDEX_SIGNER_ADDRESS: " SIGNER_ADDRESS
    read -sp "ASTERDEX_PRIVATE_KEY: " PRIVATE_KEY
    echo ""
    read -p "WEBHOOK_SECRET (optional): " WEBHOOK_SECRET

    cat > .env << EOF
# AsterDEX API Configuration
ASTERDEX_USER_ADDRESS=$USER_ADDRESS
ASTERDEX_SIGNER_ADDRESS=$SIGNER_ADDRESS
ASTERDEX_PRIVATE_KEY=$PRIVATE_KEY
ASTERDEX_BASE_URL=https://fapi.asterdex.com

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Webhook Security
WEBHOOK_SECRET=$WEBHOOK_SECRET

# Trading Defaults
DEFAULT_LEVERAGE=10
DEFAULT_MARGIN_TYPE=CROSSED

# API Limits
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RATE_LIMIT_RETRY_DELAY=2

# Logging
LOG_LEVEL=INFO
EOF

    chmod 600 .env
    echo "✅ .env file created"
else
    echo "✅ .env file already exists, skipping..."
fi

# Start application
echo ""
echo "🚀 Starting application..."
docker compose up -d

# Wait for application to start
echo "⏳ Waiting for application to start..."
sleep 10

# Check if application is running
if docker compose ps | grep -q "Up"; then
    echo "✅ Application is running!"
else
    echo "❌ Application failed to start. Check logs with: docker compose logs"
    exit 1
fi

# Create welcome page directory and copy from repository
echo "🎨 Setting up welcome page..."
mkdir -p /var/www/asterdex

# Copy welcome page from repository (always update to latest version)
if [ -f ".digitalocean/welcome.html" ]; then
    cp .digitalocean/welcome.html /var/www/asterdex/index.html
    echo "✅ Welcome page copied from repository"
else
    echo "⚠️  Warning: .digitalocean/welcome.html not found in repository"
    echo "Creating basic welcome page..."
    cat > /var/www/asterdex/index.html << 'EOF'
<!DOCTYPE html>
<html><head><title>AsterTrade API</title></head>
<body style="font-family: sans-serif; text-align: center; padding: 50px;">
<h1>⚡ AsterTrade API</h1>
<p>Automated Trading Service for AsterDEX</p>
<p><a href="/docs">API Documentation</a> | <a href="/health">Health Check</a></p>
</body></html>
EOF
    echo "✅ Basic welcome page created"
fi

# Configure Nginx
echo "🌐 Configuring Nginx..."

# Get domain name and IP
if [ ! -f "/etc/nginx/.asterdex-domain" ]; then
    read -p "Enter your domain name (e.g., astertrade.ai) or press Enter to skip: " DOMAIN_NAME
    echo "$DOMAIN_NAME" > /etc/nginx/.asterdex-domain
else
    DOMAIN_NAME=$(cat /etc/nginx/.asterdex-domain)
    echo "Using saved domain: $DOMAIN_NAME"
fi

DROPLET_IP=$(curl -s ifconfig.me)

# Build server_name directive
if [ -z "$DOMAIN_NAME" ]; then
    SERVER_NAMES="$DROPLET_IP _"
else
    SERVER_NAMES="$DOMAIN_NAME www.$DOMAIN_NAME $DROPLET_IP _"
fi

# Create Nginx configuration (always update to latest version)
cat > /etc/nginx/sites-available/asterdex-api << EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    # Accept requests for domain, IP, and any other hostname
    server_name $SERVER_NAMES;
    
    # Serve welcome page at root
    location = / {
        root /var/www/asterdex;
        try_files /index.html =404;
    }
    
    # API endpoints (accessible at /api/*)
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Direct access to API endpoints
    location ~ ^/(docs|redoc|health|openapi.json|webhook|positions|account|orders) {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Enable site (idempotent)
ln -sf /etc/nginx/sites-available/asterdex-api /etc/nginx/sites-enabled/

# Remove default site if it exists
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    rm /etc/nginx/sites-enabled/default
fi

# Test and reload nginx
if nginx -t; then
    systemctl reload nginx
    echo "✅ Nginx configured and reloaded!"
else
    echo "❌ Nginx configuration test failed!"
    exit 1
fi

# Setup SSL if domain is provided
if [ ! -z "$DOMAIN_NAME" ] && [ "$DOMAIN_NAME" != "$DROPLET_IP" ]; then
    if [ ! -d "/etc/letsencrypt/live/$DOMAIN_NAME" ]; then
        read -p "Do you want to set up SSL with Let's Encrypt? (y/n): " SETUP_SSL
        
        if [ "$SETUP_SSL" = "y" ]; then
            read -p "Enter your email for SSL certificate: " EMAIL
            certbot --nginx -d "$DOMAIN_NAME" -d "www.$DOMAIN_NAME" --non-interactive --agree-tos -m "$EMAIL" || true
            echo "✅ SSL setup attempted!"
        fi
    else
        echo "✅ SSL certificate already exists for $DOMAIN_NAME"
    fi
fi

# Configure firewall (idempotent)
echo "🔥 Configuring firewall..."
if ! ufw status | grep -q "Status: active"; then
    read -p "Do you want to configure UFW firewall? (y/n): " SETUP_FIREWALL
    
    if [ "$SETUP_FIREWALL" = "y" ]; then
        ufw allow OpenSSH
        ufw allow 'Nginx Full'
        ufw --force enable
        echo "✅ Firewall configured!"
    fi
else
    echo "✅ Firewall already active"
    # Ensure nginx is allowed
    ufw allow 'Nginx Full' 2>/dev/null || true
fi

# Print summary
echo ""
echo "=========================================="
echo "🎉 Setup Complete!"
echo "=========================================="
echo ""
echo "Your API is accessible at:"
echo ""

if [ ! -z "$DOMAIN_NAME" ] && [ "$DOMAIN_NAME" != "$DROPLET_IP" ]; then
    if [ -d "/etc/letsencrypt/live/$DOMAIN_NAME" ]; then
        echo "  🌐 https://$DOMAIN_NAME"
        echo "  🌐 https://www.$DOMAIN_NAME"
    else
        echo "  🌐 http://$DOMAIN_NAME"
        echo "  🌐 http://www.$DOMAIN_NAME"
    fi
fi

echo "  🌐 http://$DROPLET_IP"
echo ""
echo "Available endpoints:"
echo "  /              - Welcome page"
echo "  /docs          - API Documentation"
echo "  /health        - Health Check"
echo "  /webhook/...   - Webhook endpoints"
echo ""
echo "Useful commands:"
echo "  View logs:     cd /opt/asterdex-trading-api && docker compose logs -f"
echo "  Restart:       cd /opt/asterdex-trading-api && docker compose restart"
echo "  Stop:          cd /opt/asterdex-trading-api && docker compose down"
echo "  Update:        cd /opt/asterdex-trading-api && git pull && docker compose up -d --build"
echo "  Re-run setup:  bash /opt/asterdex-trading-api/.digitalocean/droplet-setup.sh"
echo ""
echo "=========================================="
