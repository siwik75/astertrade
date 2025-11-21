# Deployment Checklist

Use this checklist to ensure a smooth deployment to DigitalOcean.

## Pre-Deployment

### Code Preparation
- [ ] All code committed to Git
- [ ] Code pushed to GitHub/GitLab/Bitbucket
- [ ] `.env` file NOT committed (check `.gitignore`)
- [ ] Dockerfile tested locally
- [ ] `docker-compose.yml` tested locally
- [ ] All tests passing (if applicable)

### Credentials Ready
- [ ] `ASTERDEX_USER_ADDRESS` - Your main wallet address
- [ ] `ASTERDEX_SIGNER_ADDRESS` - Your API wallet address
- [ ] `ASTERDEX_PRIVATE_KEY` - Your API wallet private key
- [ ] `WEBHOOK_SECRET` - Generated strong secret token
- [ ] Email address for SSL certificate (if using Droplet)

### DigitalOcean Account
- [ ] DigitalOcean account created
- [ ] Payment method added
- [ ] SSH key added (if using Droplet)

---

## App Platform Deployment

### Initial Setup
- [ ] Created new App in DigitalOcean
- [ ] Connected Git repository
- [ ] Selected correct branch (main/master)
- [ ] Enabled auto-deploy on push
- [ ] Dockerfile detected automatically

### Configuration
- [ ] HTTP port set to 8000
- [ ] Selected appropriate plan ($5 or $12/month)
- [ ] Health check configured:
  - [ ] Path: `/health`
  - [ ] Port: 8000
  - [ ] Initial delay: 5 seconds
  - [ ] Period: 30 seconds

### Environment Variables
- [ ] `ASTERDEX_USER_ADDRESS` set
- [ ] `ASTERDEX_SIGNER_ADDRESS` set
- [ ] `ASTERDEX_PRIVATE_KEY` set and marked as ENCRYPTED
- [ ] `WEBHOOK_SECRET` set and marked as ENCRYPTED
- [ ] `ASTERDEX_BASE_URL` set (default: https://fapi.asterdex.com)
- [ ] `LOG_LEVEL` set to INFO or WARNING
- [ ] Optional variables configured as needed

### Deployment
- [ ] Clicked "Create Resources"
- [ ] Build completed successfully
- [ ] App deployed and running
- [ ] App URL received

---

## Droplet Deployment

### Droplet Creation
- [ ] Created Ubuntu 22.04 LTS Droplet
- [ ] Selected appropriate size ($6/month minimum)
- [ ] Selected datacenter region
- [ ] Added SSH key
- [ ] Enabled monitoring (optional)

### Server Setup
- [ ] Connected via SSH
- [ ] System updated (`apt-get update && apt-get upgrade`)
- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] Nginx installed (if using reverse proxy)
- [ ] Certbot installed (if using SSL)

### Application Deployment
- [ ] Repository cloned to `/opt/asterdex-trading-api`
- [ ] `.env` file created with credentials
- [ ] `.env` file permissions set to 600
- [ ] Application started with `docker compose up -d`
- [ ] Application running (check with `docker compose ps`)
- [ ] Logs checked for errors

### Nginx Configuration (if applicable)
- [ ] Nginx config file created
- [ ] Config file enabled
- [ ] Nginx configuration tested (`nginx -t`)
- [ ] Nginx restarted
- [ ] Application accessible via domain/IP

### SSL Configuration (if applicable)
- [ ] Domain DNS configured
- [ ] Certbot run for domain
- [ ] SSL certificate obtained
- [ ] HTTPS working
- [ ] Auto-renewal tested

### Security
- [ ] UFW firewall enabled
- [ ] SSH port allowed
- [ ] HTTP/HTTPS ports allowed
- [ ] Unnecessary ports blocked
- [ ] Root login disabled (optional but recommended)

---

## Post-Deployment Verification

### Health Checks
- [ ] Health endpoint responding: `curl https://your-url/health`
- [ ] Returns status "healthy"
- [ ] Response time acceptable (<1 second)

### API Documentation
- [ ] Swagger docs accessible: `https://your-url/docs`
- [ ] All endpoints visible
- [ ] Can test endpoints in browser

### Functionality Tests
- [ ] Account balance endpoint works: `GET /account/balance`
- [ ] Positions endpoint works: `GET /positions`
- [ ] Orders endpoint works: `GET /orders`
- [ ] Webhook endpoint accessible: `POST /webhook/tradingview`

### TradingView Integration
- [ ] Webhook URL configured in TradingView
- [ ] Webhook secret header added (if using)
- [ ] Test alert created
- [ ] Test webhook sent successfully
- [ ] Webhook received and processed
- [ ] Check logs for webhook activity

### Security Verification
- [ ] HTTPS enabled (not HTTP)
- [ ] SSL certificate valid
- [ ] Private key not exposed in logs
- [ ] Environment variables not visible in public endpoints
- [ ] Webhook secret validation working

---

## Monitoring Setup

### Basic Monitoring
- [ ] Health check endpoint monitored
- [ ] Uptime monitoring configured (UptimeRobot, Pingdom, etc.)
- [ ] Alert notifications configured
- [ ] Log aggregation set up (optional)

### DigitalOcean Monitoring
- [ ] App Platform metrics reviewed (if using App Platform)
- [ ] Droplet monitoring enabled (if using Droplet)
- [ ] CPU usage monitored
- [ ] Memory usage monitored
- [ ] Bandwidth usage monitored

### Application Monitoring
- [ ] Log level set appropriately (INFO or WARNING)
- [ ] Logs accessible and readable
- [ ] Error tracking configured (optional)
- [ ] Performance monitoring configured (optional)

---

## Production Readiness

### Performance
- [ ] Response times acceptable
- [ ] No memory leaks observed
- [ ] CPU usage reasonable
- [ ] Concurrent requests handled properly

### Reliability
- [ ] Auto-restart configured
- [ ] Health checks passing
- [ ] Error handling working
- [ ] Retry logic functioning

### Documentation
- [ ] Deployment documented
- [ ] Credentials stored securely
- [ ] Runbook created for common issues
- [ ] Team members have access

### Backup Plan
- [ ] Rollback procedure documented
- [ ] Previous version tagged in Git
- [ ] Database backup configured (if applicable)
- [ ] Disaster recovery plan in place

---

## Go-Live

### Final Checks
- [ ] All checklist items completed
- [ ] Stakeholders notified
- [ ] Monitoring active
- [ ] Support plan in place

### Initial Testing
- [ ] Small test trade executed successfully
- [ ] Position opened and closed correctly
- [ ] Webhook latency acceptable
- [ ] No errors in logs

### Gradual Rollout
- [ ] Start with small position sizes
- [ ] Monitor for 24 hours
- [ ] Gradually increase position sizes
- [ ] Monitor performance and errors

---

## Maintenance Schedule

### Daily
- [ ] Check logs for errors
- [ ] Verify health endpoint
- [ ] Monitor uptime

### Weekly
- [ ] Review performance metrics
- [ ] Check for security updates
- [ ] Review error rates

### Monthly
- [ ] Update dependencies
- [ ] Review and optimize costs
- [ ] Test disaster recovery
- [ ] Review and update documentation

---

## Troubleshooting Resources

- **Quick Start**: `.digitalocean/QUICK_START.md`
- **Full Guide**: `DIGITALOCEAN_DEPLOYMENT.md`
- **Main Docs**: `README.md`
- **API Docs**: `API_DOCUMENTATION.md`
- **Logging**: `docs/LOGGING.md`

---

## Emergency Contacts

- **DigitalOcean Support**: https://www.digitalocean.com/support
- **AsterDEX Support**: [Add contact info]
- **Team Lead**: [Add contact info]
- **On-Call Engineer**: [Add contact info]

---

**Last Updated**: [Add date when deploying]
**Deployed By**: [Add your name]
**Deployment Date**: [Add deployment date]
