# Droplet Deployment Troubleshooting

## Issue: "Attribute 'app' not found in module 'main'"

### The Problem

The Dockerfile was trying to run `uvicorn main:app` but `main.py` doesn't export an `app` object. The `app` is actually in `src/app.py`.

### The Fix

On your Droplet, run these commands:

```bash
# Navigate to your project directory
cd /opt/asterdex-trading-api

# Stop the running container
docker compose down

# Pull the latest code (if using Git)
git pull origin main

# Or manually edit the Dockerfile
nano Dockerfile
```

**Change this line:**
```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**To this:**
```dockerfile
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Also remove the version line from docker-compose.yml:**
```bash
nano docker-compose.yml
```

**Remove this line:**
```yaml
version: '3.8'
```

**Then rebuild and restart:**
```bash
# Rebuild the Docker image
docker compose build

# Start the container
docker compose up -d

# Check logs
docker compose logs -f
```

### Expected Output

You should see:
```
asterdex-trading-api  | INFO:     Started server process [1]
asterdex-trading-api  | INFO:     Waiting for application startup.
asterdex-trading-api  | INFO:     Application startup complete.
asterdex-trading-api  | INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Verify It's Working

```bash
# Test health endpoint
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","timestamp":...}
```

### If Still Having Issues

**Check environment variables:**
```bash
cat .env
```

Make sure you have:
```bash
ASTERDEX_USER_ADDRESS=0x...
ASTERDEX_SIGNER_ADDRESS=0x...
ASTERDEX_PRIVATE_KEY=0x...
```

**Check container status:**
```bash
docker compose ps
```

**View detailed logs:**
```bash
docker compose logs asterdex-api
```

**Restart from scratch:**
```bash
# Stop and remove everything
docker compose down -v

# Rebuild
docker compose build --no-cache

# Start
docker compose up -d

# Watch logs
docker compose logs -f
```

## Common Issues

### Issue: "Private key does not match signer address"

**Solution:**
```bash
# Verify your addresses match
# The private key must derive to the signer address
# See docs/ASTERDEX_ADDRESSES_EXPLAINED.md
```

### Issue: "Connection refused" to AsterDEX

**Solution:**
```bash
# Check internet connectivity
ping fapi.asterdex.com

# Check if AsterDEX is accessible
curl https://fapi.asterdex.com/fapi/v3/ping
```

### Issue: Container keeps restarting

**Solution:**
```bash
# Check logs for the error
docker compose logs asterdex-api

# Common causes:
# 1. Missing environment variables
# 2. Invalid credentials
# 3. Port already in use
```

### Issue: Port 8000 already in use

**Solution:**
```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>

# Or change the port in docker-compose.yml
# Change "8000:8000" to "8001:8000"
```

## Quick Commands Reference

```bash
# Navigate to project
cd /opt/asterdex-trading-api

# View logs
docker compose logs -f

# Restart
docker compose restart

# Stop
docker compose down

# Start
docker compose up -d

# Rebuild
docker compose build

# Full restart
docker compose down && docker compose build && docker compose up -d

# Check status
docker compose ps

# Execute command in container
docker compose exec asterdex-api bash

# View environment variables
docker compose exec asterdex-api env

# Test health endpoint
curl http://localhost:8000/health

# Test from outside (if Nginx configured)
curl https://your-domain.com/health
```

## Issue: "Account service dependency not configured"

### The Problem

The docker-compose.yml has volume mounts that override the built code with local files. This causes dependency injection to fail.

### The Fix

On your Droplet:

```bash
cd /opt/asterdex-trading-api

# Edit docker-compose.yml
nano docker-compose.yml
```

**Comment out the volumes section:**

```yaml
# volumes:
#   # Mount source code for development (comment out for production)
#   - ./src:/app/src
#   - ./main.py:/app/main.py
```

**Then rebuild:**

```bash
# Stop container
docker compose down

# Rebuild without cache
docker compose build --no-cache

# Start container
docker compose up -d

# Check logs
docker compose logs -f
```

### Expected Output

Should now work without errors:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Test

```bash
curl http://localhost:8000/account/info
# Should return account information (not 500 error)
```

## Need More Help?

1. Check main documentation: `README.md`
2. Check deployment guide: `DIGITALOCEAN_DEPLOYMENT.md`
3. Check logs: `docker compose logs -f`
4. Verify configuration: `cat .env`
