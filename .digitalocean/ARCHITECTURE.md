# Deployment Architecture

## App Platform Architecture (Recommended)

```
┌─────────────────────────────────────────────────────────────┐
│                        TradingView                          │
│                    (Webhook Sender)                         │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS POST
                         │ /webhook/tradingview
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              DigitalOcean App Platform                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  Load Balancer                        │  │
│  │              (Automatic SSL/HTTPS)                    │  │
│  └─────────────────────┬─────────────────────────────────┘  │
│                        │                                     │
│  ┌─────────────────────▼─────────────────────────────────┐  │
│  │           Your FastAPI Application                    │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │  Docker Container                            │    │  │
│  │  │  ┌────────────────────────────────────────┐  │    │  │
│  │  │  │  FastAPI App (Port 8000)               │  │    │  │
│  │  │  │  - Webhook Handler                     │  │    │  │
│  │  │  │  - Trading Service                     │  │    │  │
│  │  │  │  - Position Management                 │  │    │  │
│  │  │  │  - Account Service                     │  │    │  │
│  │  │  └────────────────────────────────────────┘  │    │  │
│  │  └──────────────────────────────────────────────┘    │  │
│  │                                                        │  │
│  │  Environment Variables (Encrypted):                   │  │
│  │  - ASTERDEX_USER_ADDRESS                              │  │
│  │  - ASTERDEX_SIGNER_ADDRESS                            │  │
│  │  - ASTERDEX_PRIVATE_KEY                               │  │
│  │  - WEBHOOK_SECRET                                     │  │
│  └────────────────────┬───────────────────────────────────┘  │
│                       │                                      │
│  ┌────────────────────▼──────────────────────────────────┐  │
│  │         Health Checks & Monitoring                    │  │
│  │         - CPU/Memory Metrics                          │  │
│  │         - Request Logs                                │  │
│  │         - Auto-restart on failure                     │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
                         │ API Calls
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    AsterDEX API                             │
│                https://fapi.asterdex.com                    │
│                                                             │
│  - Authentication (Web3 Signatures)                         │
│  - Order Execution                                          │
│  - Position Management                                      │
│  - Account Information                                      │
└─────────────────────────────────────────────────────────────┘
```

### Key Features:
- ✅ Automatic SSL/TLS
- ✅ Load balancing
- ✅ Auto-scaling
- ✅ Health monitoring
- ✅ Automatic restarts
- ✅ Built-in logging
- ✅ Zero-downtime deployments

---

## Droplet Architecture (VPS)

```
┌─────────────────────────────────────────────────────────────┐
│                        TradingView                          │
│                    (Webhook Sender)                         │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS POST
                         │ /webhook/tradingview
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  DigitalOcean Droplet                       │
│                    (Ubuntu 22.04 LTS)                       │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  Nginx (Port 80/443)                  │  │
│  │              Reverse Proxy + SSL (Let's Encrypt)     │  │
│  └─────────────────────┬─────────────────────────────────┘  │
│                        │ Proxy Pass                          │
│                        │ http://localhost:8000               │
│  ┌─────────────────────▼─────────────────────────────────┐  │
│  │              Docker Compose                           │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  Docker Container: asterdex-trading-api         │  │  │
│  │  │  ┌───────────────────────────────────────────┐  │  │  │
│  │  │  │  FastAPI App (Port 8000)                  │  │  │  │
│  │  │  │  - Webhook Handler                        │  │  │  │
│  │  │  │  - Trading Service                        │  │  │  │
│  │  │  │  - Position Management                    │  │  │  │
│  │  │  │  - Account Service                        │  │  │  │
│  │  │  └───────────────────────────────────────────┘  │  │  │
│  │  │                                                  │  │  │
│  │  │  Environment Variables (.env file):             │  │  │
│  │  │  - ASTERDEX_USER_ADDRESS                        │  │  │
│  │  │  - ASTERDEX_SIGNER_ADDRESS                      │  │  │
│  │  │  - ASTERDEX_PRIVATE_KEY                         │  │  │
│  │  │  - WEBHOOK_SECRET                               │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  UFW Firewall                         │  │
│  │  - Allow: SSH (22)                                    │  │
│  │  - Allow: HTTP (80)                                   │  │
│  │  - Allow: HTTPS (443)                                 │  │
│  │  - Deny: All other ports                              │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              System Services                          │  │
│  │  - Docker Engine                                      │  │
│  │  - Nginx                                              │  │
│  │  - Certbot (SSL renewal)                              │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
                         │ API Calls
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    AsterDEX API                             │
│                https://fapi.asterdex.com                    │
│                                                             │
│  - Authentication (Web3 Signatures)                         │
│  - Order Execution                                          │
│  - Position Management                                      │
│  - Account Information                                      │
└─────────────────────────────────────────────────────────────┘
```

### Key Features:
- ✅ Full server control
- ✅ Custom Nginx configuration
- ✅ Manual SSL with Let's Encrypt
- ✅ UFW firewall protection
- ✅ Docker containerization
- ✅ Systemd service management
- ⚠️ Manual maintenance required

---

## Request Flow

### 1. TradingView Webhook
```
TradingView Alert Triggered
    ↓
Webhook POST Request
    ↓
Headers: X-Webhook-Secret
Body: {action, symbol, side, quantity, ...}
    ↓
Your API Endpoint: /webhook/tradingview
```

### 2. API Processing
```
Webhook Received
    ↓
Validate Webhook Secret
    ↓
Parse Request Body
    ↓
Validate Trading Parameters
    ↓
Authenticate with AsterDEX (Web3 Signature)
    ↓
Execute Trading Action
    ↓
Return Response
```

### 3. AsterDEX Communication
```
Your API
    ↓
Generate Web3 Signature
    ↓
HTTPS Request to AsterDEX
    ↓
AsterDEX Validates Signature
    ↓
Execute Order/Position Action
    ↓
Return Result
    ↓
Your API Logs Result
```

---

## Data Flow

```
┌──────────────┐
│ TradingView  │
└──────┬───────┘
       │ Webhook (JSON)
       │ {action: "open", symbol: "BTCUSDT", ...}
       ▼
┌──────────────────────────────────────┐
│ Your API (DigitalOcean)              │
│                                      │
│ 1. Webhook Handler                   │
│    - Validate secret                 │
│    - Parse payload                   │
│                                      │
│ 2. Trading Service                   │
│    - Validate parameters             │
│    - Prepare order                   │
│                                      │
│ 3. AsterDEX Client                   │
│    - Generate signature              │
│    - Make API call                   │
└──────┬───────────────────────────────┘
       │ HTTPS Request
       │ Headers: X-ASTERDEX-SIGNATURE
       │ Body: Order details
       ▼
┌──────────────────────────────────────┐
│ AsterDEX API                         │
│                                      │
│ 1. Validate Signature                │
│ 2. Check Account Balance             │
│ 3. Execute Order                     │
│ 4. Update Position                   │
│ 5. Return Result                     │
└──────┬───────────────────────────────┘
       │ Response (JSON)
       │ {orderId, status, ...}
       ▼
┌──────────────────────────────────────┐
│ Your API (DigitalOcean)              │
│                                      │
│ 1. Process Response                  │
│ 2. Log Result                        │
│ 3. Return to TradingView             │
└──────────────────────────────────────┘
```

---

## Security Layers

### App Platform
```
Internet
    ↓
DigitalOcean Edge Network (DDoS Protection)
    ↓
Load Balancer (SSL/TLS Termination)
    ↓
Application Container (Isolated)
    ↓
Environment Variables (Encrypted at Rest)
    ↓
AsterDEX API (HTTPS Only)
```

### Droplet
```
Internet
    ↓
UFW Firewall (Port Filtering)
    ↓
Nginx (SSL/TLS Termination, Rate Limiting)
    ↓
Docker Container (Network Isolation)
    ↓
.env File (Restricted Permissions: 600)
    ↓
AsterDEX API (HTTPS Only)
```

---

## Scaling Considerations

### App Platform
- **Vertical Scaling**: Upgrade to larger instance size
- **Horizontal Scaling**: Increase instance count (automatic)
- **Auto-scaling**: Based on CPU/memory usage
- **Load Balancing**: Automatic across instances

### Droplet
- **Vertical Scaling**: Resize Droplet (requires downtime)
- **Horizontal Scaling**: Manual setup with load balancer
- **Auto-scaling**: Not available (manual only)
- **Load Balancing**: Requires separate load balancer Droplet

---

## Monitoring & Logging

### App Platform
```
Application Logs
    ↓
DigitalOcean Logging Service
    ↓
Dashboard Metrics
    - Request Rate
    - Response Time
    - Error Rate
    - CPU/Memory Usage
```

### Droplet
```
Application Logs (stdout/stderr)
    ↓
Docker Logs
    ↓
View with: docker compose logs -f
    ↓
Optional: Ship to external service
    - Papertrail
    - Loggly
    - ELK Stack
```

---

## Cost Optimization

### App Platform
- Start with Basic ($5/month) for testing
- Upgrade to Basic ($12/month) for production
- Scale up only when needed
- Pay for what you use

### Droplet
- Start with 1GB RAM ($6/month)
- Upgrade to 2GB RAM ($12/month) if needed
- Can run multiple services on same Droplet
- Fixed monthly cost

---

## Disaster Recovery

### App Platform
- **Automatic Backups**: Not needed (stateless app)
- **Rollback**: Deploy previous Git commit
- **High Availability**: Multi-region deployment available
- **Failover**: Automatic with multiple instances

### Droplet
- **Backups**: Enable Droplet backups (+20% cost)
- **Snapshots**: Manual snapshots before changes
- **Rollback**: Restore from snapshot or redeploy
- **High Availability**: Manual setup with floating IP

---

## Recommendation

For your AsterDEX Trading API:

### ✅ Use App Platform if:
- You want to focus on trading, not infrastructure
- You need reliable uptime for webhooks
- You want automatic scaling
- You prefer managed services

### ✅ Use Droplet if:
- You need full control over the server
- You want to run multiple services
- You're comfortable with Linux administration
- You need custom configurations

**Most users should choose App Platform** - it's easier, more reliable, and requires less maintenance.
