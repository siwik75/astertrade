#!/bin/bash
# Quick fix to add missing API routes to nginx configuration

set -e

echo "🔧 Fixing nginx configuration to include all API routes..."

# Get domain and IP
DROPLET_IP=$(curl -s ifconfig.me)
if [ -f "/etc/nginx/.asterdex-domain" ]; then
    DOMAIN_NAME=$(cat /etc/nginx/.asterdex-domain)
else
    DOMAIN_NAME=""
fi

# Build server_name directive
if [ -z "$DOMAIN_NAME" ]; then
    SERVER_NAMES="$DROPLET_IP _"
else
    SERVER_NAMES="$DOMAIN_NAME www.$DOMAIN_NAME $DROPLET_IP _"
fi

# Backup existing config
if [ -f "/etc/nginx/sites-available/asterdex-api" ]; then
    cp /etc/nginx/sites-available/asterdex-api /etc/nginx/sites-available/asterdex-api.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backed up existing config"
fi

# Create updated nginx configuration
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

echo "✅ Updated nginx configuration"

# Test nginx config
echo "🧪 Testing nginx configuration..."
if nginx -t; then
    systemctl reload nginx
    echo "✅ Nginx reloaded successfully!"
else
    echo "❌ Nginx configuration test failed!"
    echo "Restoring backup..."
    LATEST_BACKUP=$(ls -t /etc/nginx/sites-available/asterdex-api.backup.* | head -1)
    cp "$LATEST_BACKUP" /etc/nginx/sites-available/asterdex-api
    systemctl reload nginx
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Fix Complete!"
echo "=========================================="
echo ""
echo "The following routes are now accessible:"
echo "  ✅ /docs          - API documentation"
echo "  ✅ /redoc         - Alternative docs"
echo "  ✅ /health        - Health check"
echo "  ✅ /positions     - Positions API"
echo "  ✅ /account       - Account API"
echo "  ✅ /orders        - Orders API"
echo "  ✅ /webhook       - Webhook endpoints"
echo ""
echo "Test it:"
echo "  curl http://$DROPLET_IP/health"
echo "  curl http://$DROPLET_IP/docs"
echo "  curl -H 'X-API-Key: your-key' http://$DROPLET_IP/positions"
echo ""
echo "=========================================="
