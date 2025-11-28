# Using Swagger UI with API Key Authentication

## Overview

The interactive API documentation at `/docs` now shows which endpoints require authentication with a lock icon (🔒).

## Visual Guide

### Step 1: Visit /docs

Navigate to `http://your-domain/docs` in your browser.

### Step 2: Identify Protected Endpoints

Look for the lock icon (🔒) next to endpoint names:

```
🔒 GET /positions              ← Requires API key
🔒 GET /account/balance        ← Requires API key
   GET /health                 ← Public (no lock)
   GET /docs                   ← Public (no lock)
```

### Step 3: Click Authorize

At the top right of the page, click the **"Authorize"** button (🔓 lock icon).

### Step 4: Enter Your API Key

A dialog will appear with:

```
Available authorizations

X-API-Key (apiKey)
API key for accessing protected endpoints. Generate with: python generate_api_key.py

Value: [                                    ]

[Authorize] [Close]
```

Enter your API key in the "Value" field.

### Step 5: Authorize

Click the **"Authorize"** button in the dialog.

The lock icon will change from 🔓 (unlocked) to 🔒 (locked), indicating you're authenticated.

### Step 6: Close Dialog

Click **"Close"** to return to the documentation.

### Step 7: Test Endpoints

Now you can test protected endpoints:

1. Click on any endpoint (e.g., `GET /positions`)
2. Click **"Try it out"**
3. Click **"Execute"**
4. The request will include your API key automatically

## What You'll See

### Before Authorization

When you try to execute a protected endpoint without authorization:

```
Response Code: 403
Response Body:
{
  "detail": "Invalid API key"
}
```

### After Authorization

When you execute with valid authorization:

```
Response Code: 200
Response Body:
[
  {
    "symbol": "BTCUSDT",
    "position_amt": "0.001",
    ...
  }
]
```

## Lock Icons Explained

- **🔒 (Locked)** - Endpoint requires authentication, and you're authenticated
- **🔓 (Unlocked)** - Endpoint requires authentication, but you're not authenticated
- **No lock** - Endpoint is public, no authentication needed

## Logout

To remove your API key from the session:

1. Click the **"Authorize"** button again
2. Click **"Logout"** next to X-API-Key
3. Click **"Close"**

## Tips

### Tip 1: API Key Persists in Browser

Your API key is stored in your browser session. You don't need to re-enter it every time you refresh the page.

### Tip 2: Use Incognito for Testing

To test without authentication, use an incognito/private window.

### Tip 3: Check Request Headers

After executing a request, scroll down to see the actual curl command used:

```bash
curl -X 'GET' \
  'http://localhost:8000/positions' \
  -H 'accept: application/json' \
  -H 'X-API-Key: your-api-key-here'
```

This shows exactly how the API key is sent.

### Tip 4: Copy curl Command

You can copy the curl command and run it in your terminal to test outside the browser.

## Troubleshooting

### "Authorize button doesn't work"

- Make sure JavaScript is enabled in your browser
- Try refreshing the page
- Clear browser cache

### "Still getting 403 after authorizing"

- Check that you entered the correct API key
- Make sure there are no extra spaces
- Try logging out and authorizing again
- Verify the API key is set in your server's .env file

### "Lock icon doesn't appear"

- The endpoint might be public (no authentication required)
- Check the endpoint documentation to confirm if it requires authentication

### "Can't find Authorize button"

- Look at the top right of the page
- It's a button with a lock icon (🔓)
- If you don't see it, the API might not have any protected endpoints

## Example Workflow

### Testing Account Balance

1. Visit `http://localhost:8000/docs`
2. Click **"Authorize"** (top right)
3. Enter your API key
4. Click **"Authorize"**, then **"Close"**
5. Scroll to **"Account"** section
6. Click on **"GET /account/balance"** (should have 🔒 icon)
7. Click **"Try it out"**
8. Click **"Execute"**
9. See your account balance in the response

### Testing Without Authentication

1. Click **"Authorize"** (top right)
2. Click **"Logout"** next to X-API-Key
3. Click **"Close"**
4. Try to execute **"GET /account/balance"**
5. You'll get a 403 error

This confirms the endpoint is properly protected!

## Security Note

**Never share screenshots of Swagger UI that include your API key in the "Authorize" dialog or in curl commands!**

The API key is visible in:
- The Authorize dialog
- The curl command examples
- Request headers in the browser's developer tools

Always redact or blur these when sharing.

## Related Documentation

- [API_SECURITY.md](API_SECURITY.md) - Complete security guide
- [SECURITY_SETUP.md](SECURITY_SETUP.md) - Quick setup
- [API_KEY_QUICKREF.md](API_KEY_QUICKREF.md) - Quick reference
