#!/bin/bash
# Quick update script to apply nginx and welcome page changes
# Run this on your existing droplet to update configuration

set -e

echo "🔄 Updating Nginx configuration and welcome page..."

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Create welcome page directory
echo "🎨 Setting up welcome page..."
mkdir -p /var/www/asterdex

# Copy welcome page from repository
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

# Get domain and IP
DROPLET_IP=$(curl -s ifconfig.me)
if [ -f "/etc/nginx/.asterdex-domain" ]; then
    DOMAIN_NAME=$(cat /etc/nginx/.asterdex-domain)
else
    read -p "Enter your domain name (e.g., astertrade.ai) or press Enter to use IP only: " DOMAIN_NAME
    echo "$DOMAIN_NAME" > /etc/nginx/.asterdex-domain
fi

# Build server_name directive
if [ -z "$DOMAIN_NAME" ]; then
    SERVER_NAMES="$DROPLET_IP _"
else
    SERVER_NAMES="$DOMAIN_NAME www.$DOMAIN_NAME $DROPLET_IP _"
fi

echo "🌐 Updating Nginx configuration..."

# Backup existing config
if [ -f "/etc/nginx/sites-available/asterdex-api" ]; then
    cp /etc/nginx/sites-available/asterdex-api /etc/nginx/sites-available/asterdex-api.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backed up existing config"
fi

# Create new Nginx configuration
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
    
    # Direct access to docs, health, and webhook endpoints
    location ~ ^/(docs|health|openapi.json|webhook) {
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

# Enable site
ln -sf /etc/nginx/sites-available/asterdex-api /etc/nginx/sites-enabled/

# Test and reload nginx
echo "🧪 Testing Nginx configuration..."
if nginx -t; then
    systemctl reload nginx
    echo "✅ Nginx reloaded successfully!"
else
    echo "❌ Nginx configuration test failed!"
    echo "Restoring backup..."
    if [ -f "/etc/nginx/sites-available/asterdex-api.backup."* ]; then
        LATEST_BACKUP=$(ls -t /etc/nginx/sites-available/asterdex-api.backup.* | head -1)
        cp "$LATEST_BACKUP" /etc/nginx/sites-available/asterdex-api
        systemctl reload nginx
    fi
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Update Complete!"
echo "=========================================="
echo ""
echo "Your site is now accessible at:"
if [ ! -z "$DOMAIN_NAME" ]; then
    echo "  🌐 http://$DOMAIN_NAME"
    echo "  🌐 http://www.$DOMAIN_NAME"
fi
echo "  🌐 http://$DROPLET_IP"
echo ""
echo "Test the changes:"
echo "  curl http://$DROPLET_IP/"
echo "  curl http://$DROPLET_IP/health"
echo "  curl http://$DROPLET_IP/docs"
echo ""
echo "=========================================="
