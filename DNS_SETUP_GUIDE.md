# DNS Setup Guide for Droplet

## Quick Answer

**Add an A record** pointing to your Droplet's IP address.

## Step-by-Step Instructions

### 1. Get Your Droplet's IP Address

```bash
# On your Droplet, run:
curl ifconfig.me

# Or check in DigitalOcean dashboard:
# Droplets → Your Droplet → Copy the IP address
```

Example: `164.90.123.45`

---

### 2. Choose Your Domain Setup

You have two options:

#### Option A: Use Root Domain
- Domain: `yourdomain.com`
- API accessible at: `https://yourdomain.com`

#### Option B: Use Subdomain (Recommended)
- Domain: `api.yourdomain.com`
- API accessible at: `https://api.yourdomain.com`

**Recommendation:** Use a subdomain like `api.yourdomain.com` - it's cleaner and more professional.

---

### 3. Add DNS Record

Go to your domain registrar (where you bought your domain):
- Namecheap
- GoDaddy
- Google Domains
- Cloudflare
- DigitalOcean Domains
- etc.

#### For Root Domain (yourdomain.com)

| Type | Name | Value | TTL |
|------|------|-------|-----|
| **A** | **@** | **YOUR_DROPLET_IP** | **Automatic** or **300** |

Example:
- Type: `A`
- Name: `@` (or leave blank)
- Value: `164.90.123.45`
- TTL: `300` (5 minutes)

#### For Subdomain (api.yourdomain.com)

| Type | Name | Value | TTL |
|------|------|-------|-----|
| **A** | **api** | **YOUR_DROPLET_IP** | **Automatic** or **300** |

Example:
- Type: `A`
- Name: `api`
- Value: `164.90.123.45`
- TTL: `300` (5 minutes)

---

## Provider-Specific Instructions

### DigitalOcean Domains

1. Go to: https://cloud.digitalocean.com/networking/domains
2. Click your domain (or add it if not there)
3. Click "Add Record"
4. Select "A" record
5. Fill in:
   - **Hostname**: `api` (or `@` for root)
   - **Will Direct To**: Select your Droplet
   - **TTL**: 300 seconds
6. Click "Create Record"

### Namecheap

1. Log in to Namecheap
2. Go to Domain List → Manage
3. Click "Advanced DNS"
4. Click "Add New Record"
5. Fill in:
   - **Type**: A Record
   - **Host**: `api` (or `@` for root)
   - **Value**: YOUR_DROPLET_IP
   - **TTL**: Automatic
6. Click the checkmark to save

### GoDaddy

1. Log in to GoDaddy
2. Go to My Products → Domains
3. Click "DNS" next to your domain
4. Click "Add" under Records
5. Fill in:
   - **Type**: A
   - **Name**: `api` (or `@` for root)
   - **Value**: YOUR_DROPLET_IP
   - **TTL**: 600 seconds
6. Click "Save"

### Google Domains

1. Log in to Google Domains
2. Click your domain
3. Click "DNS" in the left menu
4. Scroll to "Custom resource records"
5. Fill in:
   - **Name**: `api` (or `@` for root)
   - **Type**: A
   - **TTL**: 5 minutes
   - **Data**: YOUR_DROPLET_IP
6. Click "Add"

### Cloudflare

1. Log in to Cloudflare
2. Select your domain
3. Click "DNS" in the top menu
4. Click "Add record"
5. Fill in:
   - **Type**: A
   - **Name**: `api` (or `@` for root)
   - **IPv4 address**: YOUR_DROPLET_IP
   - **TTL**: Auto
   - **Proxy status**: DNS only (gray cloud)
6. Click "Save"

**Important for Cloudflare:** Turn OFF the proxy (gray cloud, not orange) for initial setup.

---

## Verification

### 1. Wait for DNS Propagation

DNS changes take time to propagate:
- **Minimum**: 5 minutes
- **Typical**: 15-30 minutes
- **Maximum**: 24-48 hours (rare)

### 2. Check DNS Resolution

```bash
# From your computer, run:
dig api.yourdomain.com +short

# Or use nslookup:
nslookup api.yourdomain.com

# Should return your Droplet's IP address
```

**Online tools:**
- https://dnschecker.org
- https://www.whatsmydns.net

Enter your domain and check if it resolves to your Droplet IP globally.

### 3. Test HTTP First

```bash
# Once DNS resolves, test HTTP:
curl http://api.yourdomain.com/health

# Should return: {"status":"healthy",...}
```

### 4. Set Up SSL

Once HTTP works, add SSL:

```bash
# SSH into your Droplet
ssh root@YOUR_DROPLET_IP

# Run Certbot (replace with YOUR domain)
sudo certbot --nginx -d api.yourdomain.com

# Follow prompts:
# - Enter email
# - Agree to terms
# - Choose option 2 (redirect HTTP to HTTPS)
```

### 5. Test HTTPS

```bash
# Test HTTPS:
curl https://api.yourdomain.com/health

# Should return: {"status":"healthy",...}

# Test in browser:
# Visit: https://api.yourdomain.com/docs
```

---

## Common DNS Record Types (For Reference)

| Type | Purpose | Example |
|------|---------|---------|
| **A** | Points domain to IPv4 address | `api.yourdomain.com → 164.90.123.45` |
| **AAAA** | Points domain to IPv6 address | `api.yourdomain.com → 2001:db8::1` |
| **CNAME** | Points domain to another domain | `www.yourdomain.com → yourdomain.com` |
| **MX** | Mail server records | For email |
| **TXT** | Text records | For verification, SPF, DKIM |
| **NS** | Nameserver records | For DNS delegation |

**For your Droplet, you need an A record.**

---

## Multiple Subdomains (Optional)

You can add multiple subdomains pointing to the same Droplet:

| Type | Name | Value | Purpose |
|------|------|-------|---------|
| A | `api` | YOUR_DROPLET_IP | API endpoint |
| A | `dashboard` | YOUR_DROPLET_IP | Web dashboard |
| A | `docs` | YOUR_DROPLET_IP | Documentation |

Then configure Nginx to route different subdomains to different ports/apps.

---

## Troubleshooting

### DNS Not Resolving

**Check:**
```bash
# Check if DNS has propagated
dig api.yourdomain.com +short

# If returns nothing, DNS hasn't propagated yet
# Wait 15-30 minutes and try again
```

**Common issues:**
1. **Wrong record type** - Must be A record, not CNAME
2. **Wrong name** - Should be `api` not `api.yourdomain.com`
3. **Typo in IP address** - Double-check your Droplet IP
4. **TTL too high** - Lower TTL for faster propagation
5. **Cloudflare proxy** - Turn off orange cloud (use gray)

### "Connection Refused" After DNS Resolves

**Cause:** Nginx not configured for your domain

**Fix:**
```bash
# SSH into Droplet
ssh root@YOUR_DROPLET_IP

# Edit Nginx config
sudo nano /etc/nginx/sites-available/asterdex-api

# Make sure server_name matches your domain:
server_name api.yourdomain.com;

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Certificate Fails

**Error:** "Failed authorization procedure"

**Cause:** DNS not resolving yet or Nginx not configured

**Fix:**
1. Verify DNS resolves: `dig api.yourdomain.com +short`
2. Verify HTTP works: `curl http://api.yourdomain.com/health`
3. Then try SSL again: `sudo certbot --nginx -d api.yourdomain.com`

---

## Complete Setup Checklist

```bash
# 1. Get Droplet IP
curl ifconfig.me
# Note: 164.90.123.45

# 2. Add DNS A record at domain registrar
# Type: A
# Name: api
# Value: 164.90.123.45

# 3. Wait for DNS propagation (15-30 minutes)
dig api.yourdomain.com +short
# Should return: 164.90.123.45

# 4. Update Nginx config with your domain
sudo nano /etc/nginx/sites-available/asterdex-api
# Change server_name to: api.yourdomain.com

# 5. Test Nginx config
sudo nginx -t

# 6. Reload Nginx
sudo systemctl reload nginx

# 7. Test HTTP
curl http://api.yourdomain.com/health
# Should return: {"status":"healthy",...}

# 8. Get SSL certificate
sudo certbot --nginx -d api.yourdomain.com

# 9. Test HTTPS
curl https://api.yourdomain.com/health
# Should return: {"status":"healthy",...}

# 10. Test in browser
# Visit: https://api.yourdomain.com/docs
```

---

## Quick Reference

**What you need:**
- **Record Type**: A
- **Name/Host**: `api` (for subdomain) or `@` (for root)
- **Value/Points to**: Your Droplet's IP address
- **TTL**: 300 seconds (or Automatic)

**Example:**
```
Type: A
Name: api
Value: 164.90.123.45
TTL: 300
```

**Result:**
- Domain: `api.yourdomain.com`
- Points to: Your Droplet
- After SSL: `https://api.yourdomain.com`

---

## Need Help?

1. **Get your Droplet IP**: Check DigitalOcean dashboard
2. **Add A record**: At your domain registrar
3. **Wait**: 15-30 minutes for DNS propagation
4. **Verify**: `dig api.yourdomain.com +short`
5. **Configure Nginx**: Update `server_name`
6. **Get SSL**: `sudo certbot --nginx -d api.yourdomain.com`

That's it! 🚀
