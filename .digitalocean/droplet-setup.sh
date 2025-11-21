#!/bin/bash
# DigitalOcean Droplet Setup Script
# Run this on a fresh Ubuntu 22.04 Droplet

set -e

echo "🚀 Setting up AsterDEX Trading API on DigitalOcean Droplet..."

# Update system
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
apt-get install docker-compose-plugin -y

# Verify installations
echo "✅ Verifying installations..."
docker --version
docker compose version

# Install Nginx
echo "🌐 Installing Nginx..."
apt-get install nginx -y

# Install Certbot for SSL
echo "🔒 Installing Certbot..."
apt-get install certbot python3-certbot-nginx -y

# Create application directory
echo "📁 Creating application directory..."
mkdir -p /opt/asterdex-trading-api
cd /opt/asterdex-trading-api

# Prompt for repository URL
echo ""
echo "📥 Please enter your Git repository URL:"
read -p "Repository URL: " REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "❌ Repository URL is required!"
    exit 1
fi

# Clone repository
echo "📥 Cloning repository..."
git clone "$REPO_URL" .

# Create .env file
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

# Configure Nginx
echo ""
read -p "Do you want to configure Nginx reverse proxy? (y/n): " SETUP_NGINX

if [ "$SETUP_NGINX" = "y" ]; then
    read -p "Enter your domain name (or press Enter to use IP): " DOMAIN_NAME
    
    if [ -z "$DOMAIN_NAME" ]; then
        DOMAIN_NAME=$(curl -s ifconfig.me)
        echo "Using IP address: $DOMAIN_NAME"
    fi
    
    cat > /etc/nginx/sites-available/asterdex-api << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 90;
    }
}
EOF

    ln -sf /etc/nginx/sites-available/asterdex-api /etc/nginx/sites-enabled/
    nginx -t
    systemctl restart nginx
    
    echo "✅ Nginx configured!"
    
    # Setup SSL if domain is provided
    if [ "$DOMAIN_NAME" != "$(curl -s ifconfig.me)" ]; then
        read -p "Do you want to set up SSL with Let's Encrypt? (y/n): " SETUP_SSL
        
        if [ "$SETUP_SSL" = "y" ]; then
            read -p "Enter your email for SSL certificate: " EMAIL
            certbot --nginx -d "$DOMAIN_NAME" --non-interactive --agree-tos -m "$EMAIL"
            echo "✅ SSL configured!"
        fi
    fi
fi

# Configure firewall
echo ""
read -p "Do you want to configure UFW firewall? (y/n): " SETUP_FIREWALL

if [ "$SETUP_FIREWALL" = "y" ]; then
    ufw allow OpenSSH
    ufw allow 'Nginx Full'
    ufw --force enable
    echo "✅ Firewall configured!"
fi

# Print summary
echo ""
echo "=========================================="
echo "🎉 Setup Complete!"
echo "=========================================="
echo ""
echo "Your API is running at:"
if [ ! -z "$DOMAIN_NAME" ]; then
    if [ "$SETUP_SSL" = "y" ]; then
        echo "  https://$DOMAIN_NAME"
    else
        echo "  http://$DOMAIN_NAME"
    fi
else
    echo "  http://$(curl -s ifconfig.me):8000"
fi
echo ""
echo "API Documentation: /docs"
echo "Health Check: /health"
echo ""
echo "Useful commands:"
echo "  View logs:     docker compose logs -f"
echo "  Restart:       docker compose restart"
echo "  Stop:          docker compose down"
echo "  Update:        git pull && docker compose up -d --build"
echo ""
echo "=========================================="
