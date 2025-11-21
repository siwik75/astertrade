# AsterDEX Addresses Explained

## Quick Answer

**Yes, `ASTERDEX_PRIVATE_KEY` is tied to `ASTERDEX_SIGNER_ADDRESS`.**

The private key MUST match the signer address, or authentication will fail.

## The Three Components

### 1. ASTERDEX_USER_ADDRESS (Main Wallet)

**What it is:**
- Your main trading wallet address
- The account that holds your funds
- The address you registered with AsterDEX
- The address that owns your positions and balances

**Example:**
```
0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

**Purpose:**
- Identifies whose account is being accessed
- Links API requests to your trading account
- Receives profits, pays fees, holds collateral

**Think of it as:** Your bank account number

---

### 2. ASTERDEX_SIGNER_ADDRESS (API Wallet)

**What it is:**
- A separate wallet address used specifically for API authentication
- The address that signs API requests
- Derived from `ASTERDEX_PRIVATE_KEY`
- Must be authorized by your main wallet on AsterDEX

**Example:**
```
0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199
```

**Purpose:**
- Signs API requests to prove they're authorized
- Provides security through cryptographic signatures
- Can be revoked without affecting your main wallet

**Think of it as:** Your API key or authentication token

---

### 3. ASTERDEX_PRIVATE_KEY (Signer's Private Key)

**What it is:**
- The private key that corresponds to `ASTERDEX_SIGNER_ADDRESS`
- Used to create cryptographic signatures
- MUST match the signer address

**Example:**
```
0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
```

**Purpose:**
- Signs API requests with ECDSA signatures
- Proves you control the signer address
- Authenticates every API call

**Think of it as:** Your password or secret key

---

## How They Work Together

### The Authentication Flow

```
1. Your API wants to place an order
   ↓
2. API prepares request parameters
   {symbol: "BTCUSDT", side: "BUY", quantity: "0.001"}
   ↓
3. API adds authentication:
   - user: ASTERDEX_USER_ADDRESS (whose account)
   - signer: ASTERDEX_SIGNER_ADDRESS (who's signing)
   - nonce: timestamp (prevent replay attacks)
   ↓
4. API creates signature using ASTERDEX_PRIVATE_KEY:
   - ABI encode: params + user + signer + nonce
   - Keccak hash the encoded data
   - ECDSA sign with private key
   ↓
5. Send to AsterDEX:
   {
     symbol: "BTCUSDT",
     side: "BUY",
     quantity: "0.001",
     user: "0x742d35...",
     signer: "0x8626f6...",
     nonce: 1700000000000000,
     signature: "0xabcd..."
   }
   ↓
6. AsterDEX verifies:
   - Is signer authorized for this user? ✓
   - Does signature match signer address? ✓
   - Is nonce valid (not replayed)? ✓
   ↓
7. Execute trade on user's account
```

### Code Implementation

From `src/client/authenticator.py`:

```python
def __init__(self, user: str, signer: str, private_key: str):
    self.user = user.lower()
    self.signer = signer.lower()
    self.private_key = private_key
    self.account = Account.from_key(private_key)
    
    # CRITICAL: Verify signer address matches private key
    if self.account.address.lower() != self.signer:
        raise ValueError(
            f"Private key does not match signer address. "
            f"Expected: {self.signer}, Got: {self.account.address.lower()}"
        )
```

**This check ensures:**
- The private key you provide actually controls the signer address
- You can't accidentally use the wrong private key
- Authentication will work correctly

---

## Why Two Addresses?

### Security Benefits

**1. Separation of Concerns**
- Main wallet: Holds funds, can be kept in cold storage
- Signer wallet: Only for API access, can be hot wallet

**2. Limited Exposure**
- If API key (signer) is compromised, revoke it
- Main wallet funds remain safe
- No need to move funds or change main address

**3. Multiple API Keys**
- Can have multiple signer addresses for one user
- Different bots or strategies can have separate signers
- Easy to revoke individual API access

**4. Audit Trail**
- Know which API key made which trades
- Track different trading strategies separately
- Better security monitoring

### Real-World Analogy

```
ASTERDEX_USER_ADDRESS = Your bank account
ASTERDEX_SIGNER_ADDRESS = Your debit card
ASTERDEX_PRIVATE_KEY = Your PIN code

- Bank account holds your money
- Debit card accesses the account
- PIN proves you own the card
- If card is stolen, cancel it (not the whole account)
- Can have multiple cards for same account
```

---

## Setting Up Your Addresses

### Step 1: Get Your Main Wallet Address

This is your existing AsterDEX trading account:

```bash
# Your main wallet address (already registered on AsterDEX)
ASTERDEX_USER_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

### Step 2: Create API Wallet (Signer)

You need to create a NEW wallet specifically for API access:

**Option A: Using MetaMask**
1. Create a new account in MetaMask
2. Copy the address → This is your `ASTERDEX_SIGNER_ADDRESS`
3. Export private key → This is your `ASTERDEX_PRIVATE_KEY`

**Option B: Using Python**
```python
from eth_account import Account

# Create new wallet
account = Account.create()

print(f"Signer Address: {account.address}")
print(f"Private Key: {account.key.hex()}")
```

**Option C: Using Web3.js**
```javascript
const Web3 = require('web3');
const web3 = new Web3();

// Create new wallet
const account = web3.eth.accounts.create();

console.log('Signer Address:', account.address);
console.log('Private Key:', account.privateKey);
```

### Step 3: Register Signer on AsterDEX

**Important:** You must authorize the signer address on AsterDEX platform:

1. Log into AsterDEX with your main wallet
2. Go to API Management settings
3. Add your signer address as an authorized API key
4. Confirm the authorization

**Without this step, API requests will be rejected!**

### Step 4: Configure Your API

```bash
# .env file
ASTERDEX_USER_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
ASTERDEX_SIGNER_ADDRESS=0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199
ASTERDEX_PRIVATE_KEY=0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
```

---

## Verification

### How to Verify Your Setup

**1. Check Address Derivation**

```python
from eth_account import Account

# Your private key
private_key = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

# Derive address from private key
account = Account.from_key(private_key)
derived_address = account.address

print(f"Derived Address: {derived_address}")
print(f"Your Signer Address: 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199")
print(f"Match: {derived_address.lower() == '0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199'.lower()}")
```

**2. Test Authentication**

```bash
# Start your API
docker compose up -d

# Check health
curl http://localhost:8000/health

# Try to get account balance (requires authentication)
curl http://localhost:8000/account/balance

# If you see balance data → Authentication works! ✓
# If you see 401/403 error → Check your addresses
```

**3. Check Logs**

```bash
docker compose logs | grep "authenticator_initialized"

# Should see:
# authenticator_initialized user=0x742d35... signer=0x8626f6...
```

---

## Common Mistakes

### Mistake 1: Using Main Wallet's Private Key

❌ **Wrong:**
```bash
ASTERDEX_USER_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
ASTERDEX_SIGNER_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb  # Same!
ASTERDEX_PRIVATE_KEY=0x[main wallet private key]
```

**Problem:** Exposes your main wallet's private key to the API server

✅ **Correct:**
```bash
ASTERDEX_USER_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
ASTERDEX_SIGNER_ADDRESS=0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199  # Different!
ASTERDEX_PRIVATE_KEY=0x[signer wallet private key]
```

### Mistake 2: Mismatched Private Key

❌ **Wrong:**
```bash
ASTERDEX_SIGNER_ADDRESS=0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199
ASTERDEX_PRIVATE_KEY=0x[different wallet's private key]
```

**Error:**
```
ValueError: Private key does not match signer address.
Expected: 0x8626f6..., Got: 0x1234567...
```

✅ **Correct:** Private key must derive to the signer address

### Mistake 3: Not Registering Signer

❌ **Wrong:** Create signer wallet but don't register it on AsterDEX

**Error:**
```
AsterDEXClientError: Signer not authorized for this user
```

✅ **Correct:** Register signer address in AsterDEX API settings

### Mistake 4: Swapping User and Signer

❌ **Wrong:**
```bash
ASTERDEX_USER_ADDRESS=0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199  # Signer!
ASTERDEX_SIGNER_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb  # User!
```

**Problem:** API will try to trade on signer's account (which has no funds)

✅ **Correct:** User = main account, Signer = API key

---

## Security Best Practices

### 1. Keep Private Keys Secure

```bash
# ✅ Good: Environment variables
ASTERDEX_PRIVATE_KEY=0xabcd...

# ✅ Good: Encrypted in DigitalOcean
# Mark as "Encrypted" in App Platform settings

# ❌ Bad: Hardcoded in code
private_key = "0xabcd..."  # Never do this!

# ❌ Bad: Committed to Git
# .env file should be in .gitignore
```

### 2. Use Separate Signer Wallet

```bash
# ✅ Good: Different addresses
USER=0x742d35...
SIGNER=0x8626f6...

# ❌ Bad: Same address
USER=0x742d35...
SIGNER=0x742d35...  # Exposes main wallet!
```

### 3. Limit Signer Permissions

On AsterDEX platform:
- ✅ Only grant necessary permissions to signer
- ✅ Set withdrawal limits if available
- ✅ Enable IP whitelisting if available
- ✅ Monitor signer activity regularly

### 4. Rotate Signers Periodically

```bash
# Every 3-6 months:
1. Create new signer wallet
2. Register new signer on AsterDEX
3. Update API configuration
4. Test new signer works
5. Revoke old signer on AsterDEX
```

### 5. Monitor for Unauthorized Access

```bash
# Check logs for authentication failures
docker compose logs | grep "signer_address_mismatch"
docker compose logs | grep "authentication_failed"

# Review trades regularly
curl http://localhost:8000/orders | jq
```

---

## Troubleshooting

### Error: "Private key does not match signer address"

**Cause:** The private key you provided doesn't derive to the signer address

**Solution:**
1. Verify private key is correct
2. Derive address from private key (see Verification section)
3. Update `ASTERDEX_SIGNER_ADDRESS` to match derived address

### Error: "Signer not authorized"

**Cause:** Signer address not registered on AsterDEX for your user

**Solution:**
1. Log into AsterDEX with main wallet
2. Go to API Management
3. Add signer address as authorized API key
4. Wait a few minutes for authorization to propagate

### Error: "Invalid signature"

**Cause:** Signature verification failed on AsterDEX side

**Possible reasons:**
- Signer not properly authorized
- Clock skew (timestamp too far off)
- Wrong private key being used

**Solution:**
1. Verify signer is authorized on AsterDEX
2. Check system time is synchronized
3. Verify private key matches signer address
4. Check API logs for detailed error

---

## Summary

### The Relationship

```
ASTERDEX_USER_ADDRESS
    ↓ (owns)
Trading Account (funds, positions, balances)
    ↑ (accessed by)
ASTERDEX_SIGNER_ADDRESS
    ↑ (controlled by)
ASTERDEX_PRIVATE_KEY
```

### Key Points

1. **User Address** = Your trading account (holds funds)
2. **Signer Address** = Your API key (signs requests)
3. **Private Key** = Proves you control the signer
4. **Private key MUST match signer address** (verified on startup)
5. **Signer must be authorized** by user on AsterDEX platform
6. **Use separate wallets** for user and signer (security)

### Quick Check

```bash
# Verify your setup:
1. User address = Your main AsterDEX account? ✓
2. Signer address = New wallet created for API? ✓
3. Private key derives to signer address? ✓
4. Signer registered on AsterDEX platform? ✓
5. All three configured in .env file? ✓
```

If all checks pass, you're good to go! 🚀
