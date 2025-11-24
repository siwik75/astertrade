# Signature Check Failed - Troubleshooting

## Error: "Signature check failed" (-1000)

This error means AsterDEX is rejecting your signature. Here are the most common causes:

### 1. Signer Not Registered on AsterDEX (Most Common)

**Problem:** Your signer address isn't authorized to access your user account on AsterDEX.

**Solution:**
1. Log into AsterDEX with your **main wallet** (ASTERDEX_USER_ADDRESS)
2. Go to **API Management** or **Settings**
3. Look for **API Keys** or **Authorized Signers**
4. Add your **ASTERDEX_SIGNER_ADDRESS** as an authorized API key
5. Save and wait a few minutes for it to propagate

**How to verify:**
- Your signer address should appear in the list of authorized API keys
- The status should be "Active" or "Enabled"

---

### 2. Wrong Addresses in .env File

**Problem:** The addresses in your .env file don't match what's registered on AsterDEX.

**Check your .env file:**
```bash
cat .env | grep ASTERDEX
```

**Verify:**
- `ASTERDEX_USER_ADDRESS` = Your main trading wallet (the one you use to log into AsterDEX)
- `ASTERDEX_SIGNER_ADDRESS` = The API wallet you created for signing
- `ASTERDEX_PRIVATE_KEY` = The private key that derives to ASTERDEX_SIGNER_ADDRESS

**Test if private key matches signer:**
```python
from eth_account import Account

private_key = "0xYOUR_PRIVATE_KEY"
account = Account.from_key(private_key)

print(f"Derived address: {account.address}")
print(f"Your signer:     0xYOUR_SIGNER_ADDRESS")
print(f"Match: {account.address.lower() == '0xYOUR_SIGNER_ADDRESS'.lower()}")
```

---

### 3. Addresses Not Checksummed Correctly

**Problem:** Ethereum addresses are case-sensitive in some contexts.

**Solution:** Make sure addresses are lowercase in your .env:
```bash
# Good
ASTERDEX_USER_ADDRESS=0x742d35cc6634c0532925a3b844bc9e7595f0beb
ASTERDEX_SIGNER_ADDRESS=0x8626f6940e2eb28930efb4cef49b2d1f2c9c1199

# Also OK (will be converted to lowercase)
ASTERDEX_USER_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

---

### 4. Enable Debug Logging

To see what's being signed, enable debug logging:

**Edit .env:**
```bash
LOG_LEVEL=DEBUG
```

**Restart:**
```bash
docker compose down
docker compose up -d
docker compose logs -f
```

**Look for these log entries:**
```
signing_request param_string=... user=... signer=... nonce=...
message_hash_generated message_hash=0x...
signature_generated signature=0x...
```

This will show you exactly what's being sent to AsterDEX.

---

### 5. Check AsterDEX API Status

**Problem:** AsterDEX API might be having issues.

**Test:**
```bash
# Test if AsterDEX API is accessible
curl https://fapi.asterdex.com/fapi/v3/ping

# Should return: {"code":0,"msg":"pong"}
```

---

### 6. Time Synchronization

**Problem:** Your server's clock is off, causing timestamp issues.

**Check server time:**
```bash
date
timedatectl status
```

**Sync time if needed:**
```bash
sudo timedatectl set-ntp true
sudo systemctl restart systemd-timesyncd
```

---

### 7. Parameter Encoding Issues

**Problem:** Parameters aren't being encoded correctly.

**Check the logs for the param_string:**
```bash
docker compose logs | grep "signing_request"
```

Should show something like:
```
param_string={"recvWindow":"5000","symbol":"BTCUSDT","timestamp":"1700000000000"}
```

Parameters should be:
- Sorted alphabetically by key
- All values as strings
- No spaces in JSON

---

## Step-by-Step Verification

### Step 1: Verify Your Addresses

```bash
# On your Droplet
cd /opt/asterdex-trading-api
cat .env | grep ASTERDEX_USER_ADDRESS
cat .env | grep ASTERDEX_SIGNER_ADDRESS
```

Write these down:
- User Address: `0x...`
- Signer Address: `0x...`

### Step 2: Verify Signer is Registered

1. Go to AsterDEX website
2. Connect with your **User Address** wallet
3. Navigate to API Management / Settings
4. Check if your **Signer Address** is listed
5. If not, add it and enable it

### Step 3: Verify Private Key Matches Signer

```bash
# On your Droplet, check the logs when the app starts
docker compose logs | grep "authenticator_initialized"

# Should show:
# authenticator_initialized user=0x... signer=0x...
```

If you see an error about "Private key does not match signer address", your private key is wrong.

### Step 4: Test with Debug Logging

```bash
# Edit .env
nano .env

# Change LOG_LEVEL to DEBUG
LOG_LEVEL=DEBUG

# Restart
docker compose restart

# Test
curl http://localhost:8000/account/info

# Check logs
docker compose logs | tail -50
```

Look for any errors or warnings in the signature generation process.

---

## Common Scenarios

### Scenario 1: Fresh Setup

**If you just set up the API:**
1. ✅ Created signer wallet
2. ❌ **Forgot to register signer on AsterDEX**
3. Result: Signature check failed

**Fix:** Register signer on AsterDEX platform

### Scenario 2: Using Main Wallet as Signer

**If you used the same address for both:**
```bash
ASTERDEX_USER_ADDRESS=0x742d35...
ASTERDEX_SIGNER_ADDRESS=0x742d35...  # Same!
```

**This might work, but:**
- Less secure (exposes main wallet private key)
- May still need to register as API key on AsterDEX

**Better:** Create separate signer wallet

### Scenario 3: Copied Wrong Private Key

**If you have multiple wallets:**
- Make sure the private key belongs to the signer address
- Not the user address
- Not some other wallet

**Verify:**
```python
from eth_account import Account
account = Account.from_key("0xYOUR_PRIVATE_KEY")
print(account.address)  # Should match ASTERDEX_SIGNER_ADDRESS
```

---

## Quick Fix Checklist

Run through this checklist:

```bash
# 1. Check addresses are set
cat .env | grep ASTERDEX_USER_ADDRESS
cat .env | grep ASTERDEX_SIGNER_ADDRESS
cat .env | grep ASTERDEX_PRIVATE_KEY

# 2. Check app started without errors
docker compose logs | grep "authenticator_initialized"
# Should NOT see "Private key does not match"

# 3. Check signer is registered on AsterDEX
# (Do this in AsterDEX web interface)

# 4. Enable debug logging
echo "LOG_LEVEL=DEBUG" >> .env
docker compose restart

# 5. Test and check logs
curl http://localhost:8000/account/info
docker compose logs | tail -100
```

---

## Still Not Working?

If you've verified everything above and it still doesn't work:

1. **Double-check signer registration on AsterDEX**
   - This is the #1 cause of signature failures
   - Make sure it's enabled/active
   - Wait 5-10 minutes after registering

2. **Try with a fresh signer wallet**
   ```python
   from eth_account import Account
   new_account = Account.create()
   print(f"New Signer: {new_account.address}")
   print(f"Private Key: {new_account.key.hex()}")
   ```
   - Register this new signer on AsterDEX
   - Update your .env file
   - Restart and test

3. **Contact AsterDEX Support**
   - Provide your user address
   - Provide your signer address
   - Ask them to verify the signer is properly registered

---

## Success Indicators

When everything is working, you should see:

```bash
# In logs:
authenticator_initialized user=0x742d35... signer=0x8626f6...
asterdex_api_request method=GET endpoint=/fapi/v3/account
asterdex_api_response method=GET endpoint=/fapi/v3/account status_code=200

# In response:
curl http://localhost:8000/account/info
# Returns JSON with account data (not error)
```

---

## Most Likely Solution

**90% of the time, the issue is:**

**Signer address not registered on AsterDEX platform.**

**Fix:**
1. Log into AsterDEX with your main wallet
2. Go to API Management
3. Add your signer address
4. Enable it
5. Wait 5 minutes
6. Try again

That's it! 🚀
