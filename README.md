# AsterDEX Trading API

A FastAPI-based microservice that bridges TradingView webhook signals with the AsterDEX perpetual futures trading platform. This server handles authentication, order execution, position management, and provides RESTful endpoints for querying account information.

## Features

- 🔐 **Secure Authentication**: Web3-based ECDSA signature authentication with AsterDEX API
- 📊 **TradingView Integration**: Receive and process webhook signals for automated trading
- 💼 **Position Management**: Open, increase, decrease, and close positions programmatically
- 📈 **Account Monitoring**: Query balances, positions, and order history
- 🔄 **Retry Logic**: Automatic retry with exponential backoff for rate limits and server errors
- 📝 **Structured Logging**: JSON-formatted logs for easy parsing and monitoring
- 📚 **Interactive Documentation**: Auto-generated OpenAPI/Swagger docs at `/docs`

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Server](#running-the-server)
- [Deployment](#deployment)
- [TradingView Webhook Setup](#tradingview-webhook-setup)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)

## Requirements

- Python 3.11 or higher
- AsterDEX account with API credentials (user address, signer address, private key)
- TradingView account (for webhook integration)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd asterdex-trading-api
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   Or using the package:
   ```bash
   pip install -e .
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your AsterDEX credentials (see [Configuration](#configuration) below)

## Configuration

All configuration is managed through environment variables. Copy `.env.example` to `.env` and configure the following:

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ASTERDEX_USER_ADDRESS` | Your main wallet address registered on AsterDEX | `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb` |
| `ASTERDEX_SIGNER_ADDRESS` | Your API wallet address (signer) | `0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199` |
| `ASTERDEX_PRIVATE_KEY` | Your API wallet private key (keep secure!) | `0xabcdef123456...` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ASTERDEX_BASE_URL` | AsterDEX API base URL | `https://fapi.asterdex.com` |
| `SERVER_HOST` | Server bind address | `0.0.0.0` |
| `SERVER_PORT` | Server port | `8000` |
| `WEBHOOK_SECRET` | Secret token for webhook validation | (none) |
| `DEFAULT_LEVERAGE` | Default leverage for new positions | `10` |
| `DEFAULT_MARGIN_TYPE` | Default margin type (ISOLATED/CROSSED) | `CROSSED` |
| `REQUEST_TIMEOUT` | API request timeout in seconds | `30` |
| `MAX_RETRIES` | Maximum retry attempts for failed requests | `3` |
| `RATE_LIMIT_RETRY_DELAY` | Initial delay for rate limit retries (seconds) | `2` |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | `INFO` |

### Security Notes

- **Never commit your `.env` file** to version control
- Store `ASTERDEX_PRIVATE_KEY` securely (use secrets management in production)
- Set `WEBHOOK_SECRET` to validate incoming TradingView webhooks
- Use HTTPS in production environments

## Running the Server

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
# Run with multiple workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker

```bash
# Build the image
docker build -t asterdex-trading-api .

# Run the container
docker run -d \
  --name asterdex-api \
  -p 8000:8000 \
  --env-file .env \
  asterdex-trading-api
```

### Verify Server is Running

Once started, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Deployment

### Docker Deployment

The recommended way to deploy the AsterDEX Trading API is using Docker and Docker Compose.

#### Prerequisites

- Docker 20.10 or higher
- Docker Compose 2.0 or higher

#### Quick Start with Docker Compose

1. **Clone the repository and configure environment**
   ```bash
   git clone <repository-url>
   cd asterdex-trading-api
   cp .env.example .env
   # Edit .env with your AsterDEX credentials
   ```

2. **Build and start the service**
   ```bash
   docker-compose up -d
   ```

3. **Check service status**
   ```bash
   docker-compose ps
   docker-compose logs -f asterdex-api
   ```

4. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

5. **Stop the service**
   ```bash
   docker-compose down
   ```

#### Docker Compose Configuration

The `docker-compose.yml` file includes:
- Automatic container restart on failure
- Health checks every 30 seconds
- Environment variable configuration
- Volume mounts for development (optional)
- Network isolation

#### Production Docker Deployment

For production, modify `docker-compose.yml`:

1. **Remove development volume mounts**
   ```yaml
   # Comment out or remove these lines:
   # volumes:
   #   - ./src:/app/src
   #   - ./main.py:/app/main.py
   ```

2. **Add resource limits**
   ```yaml
   services:
     asterdex-api:
       # ... existing config ...
       deploy:
         resources:
           limits:
             cpus: '1.0'
             memory: 512M
           reservations:
             cpus: '0.5'
             memory: 256M
   ```

3. **Use production-grade logging**
   ```yaml
   services:
     asterdex-api:
       # ... existing config ...
       logging:
         driver: "json-file"
         options:
           max-size: "10m"
           max-file: "3"
   ```

#### Manual Docker Build and Run

If you prefer not to use Docker Compose:

```bash
# Build the image
docker build -t asterdex-trading-api:latest .

# Run the container
docker run -d \
  --name asterdex-api \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  asterdex-trading-api:latest

# View logs
docker logs -f asterdex-api

# Stop and remove container
docker stop asterdex-api
docker rm asterdex-api
```

#### Docker Image Details

The Dockerfile:
- Uses Python 3.11 slim base image for minimal size
- Installs only necessary system dependencies
- Includes health check configuration
- Runs as non-root user (security best practice)
- Exposes port 8000

### Cloud Deployment

#### AWS ECS/Fargate

1. **Push image to ECR**
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   docker tag asterdex-trading-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/asterdex-trading-api:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/asterdex-trading-api:latest
   ```

2. **Create ECS task definition** with environment variables from AWS Secrets Manager

3. **Deploy to Fargate** with Application Load Balancer for HTTPS

#### Google Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/asterdex-trading-api

# Deploy to Cloud Run
gcloud run deploy asterdex-trading-api \
  --image gcr.io/PROJECT-ID/asterdex-trading-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ASTERDEX_USER_ADDRESS=0x...,ASTERDEX_SIGNER_ADDRESS=0x... \
  --set-secrets ASTERDEX_PRIVATE_KEY=asterdex-key:latest
```

#### DigitalOcean App Platform

1. Connect your GitHub repository
2. Configure environment variables in the dashboard
3. Use the Dockerfile for deployment
4. Enable automatic deployments on push

#### Heroku

```bash
# Login to Heroku
heroku login

# Create app
heroku create asterdex-trading-api

# Set environment variables
heroku config:set ASTERDEX_USER_ADDRESS=0x...
heroku config:set ASTERDEX_SIGNER_ADDRESS=0x...
heroku config:set ASTERDEX_PRIVATE_KEY=0x...

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

### VPS Deployment (Ubuntu/Debian)

#### Using Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Clone and deploy
git clone <repository-url>
cd asterdex-trading-api
cp .env.example .env
# Edit .env with your credentials
sudo docker-compose up -d
```

#### Using systemd (without Docker)

1. **Install Python and dependencies**
   ```bash
   sudo apt-get update
   sudo apt-get install python3.11 python3.11-venv python3-pip
   ```

2. **Set up application**
   ```bash
   cd /opt
   sudo git clone <repository-url> asterdex-trading-api
   cd asterdex-trading-api
   sudo python3.11 -m venv venv
   sudo venv/bin/pip install -r requirements.txt
   sudo cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Create systemd service**
   ```bash
   sudo nano /etc/systemd/system/asterdex-api.service
   ```
   
   Add:
   ```ini
   [Unit]
   Description=AsterDEX Trading API
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/opt/asterdex-trading-api
   Environment="PATH=/opt/asterdex-trading-api/venv/bin"
   EnvironmentFile=/opt/asterdex-trading-api/.env
   ExecStart=/opt/asterdex-trading-api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

4. **Start service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable asterdex-api
   sudo systemctl start asterdex-api
   sudo systemctl status asterdex-api
   ```

5. **Set up Nginx reverse proxy**
   ```bash
   sudo apt-get install nginx
   sudo nano /etc/nginx/sites-available/asterdex-api
   ```
   
   Add:
   ```nginx
   server {
       listen 80;
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
   
   Enable and restart:
   ```bash
   sudo ln -s /etc/nginx/sites-available/asterdex-api /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

6. **Set up SSL with Let's Encrypt**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

### Deployment Checklist

Before deploying to production:

- [ ] Set strong `WEBHOOK_SECRET` for webhook validation
- [ ] Use HTTPS/TLS for all connections
- [ ] Store `ASTERDEX_PRIVATE_KEY` in secrets manager (AWS Secrets Manager, Google Secret Manager, etc.)
- [ ] Set `LOG_LEVEL=INFO` or `WARNING` (not DEBUG)
- [ ] Configure firewall to allow only necessary ports
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation (CloudWatch, Stackdriver, etc.)
- [ ] Enable health check monitoring
- [ ] Set up automated backups if storing any data
- [ ] Test webhook connectivity from TradingView
- [ ] Verify API authentication with AsterDEX
- [ ] Set appropriate resource limits (CPU, memory)
- [ ] Configure auto-scaling if needed
- [ ] Document rollback procedures
- [ ] Set up CI/CD pipeline for automated deployments

### Monitoring and Maintenance

#### Health Checks

The API includes a health check endpoint at `/health`:
```bash
curl http://your-domain.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": 1699999999999,
  "version": "1.0.0"
}
```

#### Monitoring Metrics

Key metrics to monitor:
- Request rate and response times
- Error rates by endpoint
- AsterDEX API call success/failure rates
- Order execution success rates
- Position PnL tracking
- Memory and CPU usage
- Container restart count

#### Log Management

View logs:
```bash
# Docker Compose
docker-compose logs -f asterdex-api

# Docker
docker logs -f asterdex-api

# Systemd
sudo journalctl -u asterdex-api -f
```

#### Updating the Application

```bash
# Docker Compose
git pull
docker-compose down
docker-compose build
docker-compose up -d

# Systemd
cd /opt/asterdex-trading-api
sudo git pull
sudo venv/bin/pip install -r requirements.txt
sudo systemctl restart asterdex-api
```

## TradingView Webhook Setup

### 1. Configure Webhook URL

In TradingView alert settings, set the webhook URL to:
```
http://your-server-address:8000/webhook/tradingview
```

### 2. Webhook Payload Examples

#### Open a Long Position (Market Order)
```json
{
  "action": "open",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "quantity": "0.001",
  "order_type": "MARKET"
}
```

#### Open a Short Position (Limit Order)
```json
{
  "action": "open",
  "symbol": "ETHUSDT",
  "side": "SELL",
  "quantity": "0.01",
  "order_type": "LIMIT",
  "price": "2000.50"
}
```

#### Increase Existing Position
```json
{
  "action": "increase",
  "symbol": "BTCUSDT",
  "quantity": "0.001",
  "order_type": "MARKET"
}
```

#### Decrease Position (Partial Close)
```json
{
  "action": "decrease",
  "symbol": "BTCUSDT",
  "quantity": "0.0005",
  "order_type": "MARKET"
}
```

#### Close Entire Position
```json
{
  "action": "close",
  "symbol": "BTCUSDT"
}
```

### 3. Add Webhook Secret (Optional)

If you set `WEBHOOK_SECRET` in your `.env` file, add it as a custom header in TradingView:
- Header Name: `X-Webhook-Secret`
- Header Value: `your-secret-token`

## API Endpoints

### Health & Documentation

#### GET /
Redirects to interactive API documentation

#### GET /health
Health check endpoint
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": 1699999999999,
  "version": "1.0.0"
}
```

#### GET /docs
Interactive Swagger UI documentation

### Webhook

#### POST /webhook/tradingview
Receive TradingView webhook and execute trading action

```bash
curl -X POST http://localhost:8000/webhook/tradingview \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secret" \
  -d '{
    "action": "open",
    "symbol": "BTCUSDT",
    "side": "BUY",
    "quantity": "0.001",
    "order_type": "MARKET"
  }'
```

### Positions

#### GET /positions
Get all open positions
```bash
curl http://localhost:8000/positions
```

#### GET /positions/{symbol}
Get position for specific symbol
```bash
curl http://localhost:8000/positions/BTCUSDT
```

#### POST /positions/{symbol}/leverage
Update leverage for symbol
```bash
curl -X POST http://localhost:8000/positions/BTCUSDT/leverage \
  -H "Content-Type: application/json" \
  -d '{"leverage": 20}'
```

#### POST /positions/{symbol}/margin-type
Update margin type for symbol
```bash
curl -X POST http://localhost:8000/positions/BTCUSDT/margin-type \
  -H "Content-Type: application/json" \
  -d '{"margin_type": "ISOLATED"}'
```

### Account

#### GET /account/balance
Get account balance
```bash
curl http://localhost:8000/account/balance
```

#### GET /account/info
Get full account information
```bash
curl http://localhost:8000/account/info
```

### Orders

#### GET /orders
Get order history with optional filters
```bash
# Get all orders for a symbol
curl "http://localhost:8000/orders?symbol=BTCUSDT&limit=50"

# Get orders within time range
curl "http://localhost:8000/orders?symbol=BTCUSDT&startTime=1699900000000&endTime=1699999999999"
```

#### GET /orders/open
Get open orders
```bash
# All open orders
curl http://localhost:8000/orders/open

# Open orders for specific symbol
curl "http://localhost:8000/orders/open?symbol=BTCUSDT"
```

## Troubleshooting

### Common Issues

#### 1. Authentication Errors

**Problem**: `401 Unauthorized` or signature validation errors

**Solutions**:
- Verify `ASTERDEX_USER_ADDRESS`, `ASTERDEX_SIGNER_ADDRESS`, and `ASTERDEX_PRIVATE_KEY` are correct
- Ensure private key includes the `0x` prefix
- Check that your API wallet is properly registered on AsterDEX
- Verify system time is synchronized (signature includes timestamp)

#### 2. Connection Errors

**Problem**: `Cannot connect to AsterDEX API` or timeout errors

**Solutions**:
- Check `ASTERDEX_BASE_URL` is correct
- Verify internet connectivity
- Check if AsterDEX API is operational
- Increase `REQUEST_TIMEOUT` if needed
- Check firewall settings

#### 3. Position Not Found

**Problem**: `404 Position not found` when trying to increase/decrease/close

**Solutions**:
- Verify you have an open position for the symbol
- Check position using `GET /positions/{symbol}` endpoint
- Ensure symbol format matches AsterDEX (e.g., `BTCUSDT` not `BTC-USDT`)

#### 4. Invalid Quantity

**Problem**: `400 Invalid quantity` or order rejection

**Solutions**:
- Check minimum order quantity for the symbol
- Verify quantity precision (decimal places)
- Use `GET /positions/{symbol}` to check current position size before decreasing
- Consult AsterDEX exchange info for symbol requirements

#### 5. Rate Limit Errors

**Problem**: `429 Too Many Requests`

**Solutions**:
- The server automatically retries with exponential backoff
- Reduce webhook frequency in TradingView
- Increase `RATE_LIMIT_RETRY_DELAY` for longer initial delays
- Check `MAX_RETRIES` setting

#### 6. Webhook Not Triggering

**Problem**: TradingView webhook not executing trades

**Solutions**:
- Verify webhook URL is publicly accessible (use ngrok for local testing)
- Check TradingView alert is active and webhook is configured
- Verify `X-Webhook-Secret` header matches `WEBHOOK_SECRET` if configured
- Check server logs for incoming requests: `docker logs asterdex-api`
- Test webhook manually with curl

#### 7. Leverage/Margin Type Changes Fail

**Problem**: Cannot change leverage or margin type

**Solutions**:
- Close all open positions before changing margin type
- Ensure leverage is between 1 and 125
- Check if symbol supports the requested leverage
- Verify margin type is either `ISOLATED` or `CROSSED`

### Logging and Debugging

#### View Logs

```bash
# If running with uvicorn
# Logs output to console

# If running with Docker
docker logs asterdex-api

# Follow logs in real-time
docker logs -f asterdex-api
```

#### Enable Debug Logging

Set in `.env`:
```bash
LOG_LEVEL=DEBUG
```

#### Check Health Status

```bash
curl http://localhost:8000/health
```

### Getting Help

- Check the interactive API documentation at `/docs`
- Review logs for detailed error messages
- Consult AsterDEX API documentation
- Verify all environment variables are set correctly

## Project Structure

```
asterdex-trading-api/
├── src/
│   ├── __init__.py
│   ├── app.py                 # FastAPI application setup
│   ├── config.py              # Configuration management
│   ├── logging_config.py      # Structured logging setup
│   ├── exceptions.py          # Custom exception classes
│   ├── error_handlers.py      # Global error handlers
│   ├── client/
│   │   ├── __init__.py
│   │   ├── authenticator.py   # AsterDEX authentication
│   │   └── asterdex_client.py # AsterDEX API client
│   ├── services/
│   │   ├── __init__.py
│   │   ├── trading_service.py # Trading business logic
│   │   ├── position_service.py# Position management
│   │   └── account_service.py # Account operations
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py        # Request Pydantic models
│   │   └── responses.py       # Response Pydantic models
│   └── api/
│       ├── __init__.py
│       ├── webhook.py         # Webhook endpoints
│       ├── positions.py       # Position endpoints
│       ├── account.py         # Account endpoints
│       ├── orders.py          # Order endpoints
│       └── health.py          # Health check endpoints
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── test_app.py
│   ├── test_config.py
│   ├── test_error_handling.py
│   └── test_logging.py
├── docs/
│   └── LOGGING.md            # Logging documentation
├── .kiro/
│   └── specs/                # Feature specifications
├── main.py                   # Application entry point
├── pyproject.toml           # Project metadata
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## License

See [LICENSE](LICENSE) file for details.

## Contributing

This project follows the spec-driven development methodology. Implementation tasks are tracked in `.kiro/specs/asterdex-trading-api/tasks.md`.

