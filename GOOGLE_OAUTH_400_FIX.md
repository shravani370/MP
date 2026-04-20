# Google OAuth 400 Bad Request - Diagnostic Guide

## Error: `400 Client Error: Bad Request for url: https://oauth2.googleapis.com/token`

This error occurs during token exchange - when your app sends the authorization code to Google to get an access token.

## Most Common Causes

### 1. ❌ Redirect URI Mismatch (60% of cases)
The redirect URI in your code **must match exactly** what's configured in Google Cloud Console.

**Check in Google Console:**
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Select your project
3. Go to **APIs & Services** → **Credentials**
4. Click your OAuth 2.0 Client ID
5. Check **Authorized redirect URIs** section

**Common mistakes:**
```
❌ WRONG:  http://127.0.0.1:5000/callback/
❌ WRONG:  http://localhost:5000/callback
❌ WRONG:  http://127.0.0.1:5000/
✅ RIGHT: http://127.0.0.1:5000/callback
```

**Verify your .env file:**
```bash
# Must match Google Console EXACTLY
REDIRECT_URI=http://127.0.0.1:5000/callback
```

### 2. ❌ Authorization Code Already Used
Authorization codes expire quickly (~10 minutes) and can only be used ONCE.

**Symptoms:**
- First attempt works
- Refreshing the callback URL fails
- Multiple rapid login attempts fail

**Solution:**
- Clear browser cookies
- Try login flow again from the beginning
- Don't manually copy/paste callback URLs

### 3. ❌ Invalid or Expired Credentials
Your Google credentials might be invalid or revoked.

**Check in your .env file:**
```bash
# These must be valid and not expired
GOOGLE_CLIENT_ID=your_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_secret_key
```

**Regenerate credentials:**
1. Go to Google Cloud Console
2. Delete existing OAuth 2.0 Client ID
3. Create a new one
4. Download new credentials
5. Update `.env` file

### 4. ❌ Missing or Malformed Parameters
The token request needs all required fields.

**Required parameters (all must be present):**
- `code` - authorization code from Google
- `client_id` - your client ID
- `client_secret` - your client secret
- `redirect_uri` - must match authorization request
- `grant_type` - must be "authorization_code"

## Diagnostic Steps

### Step 1: Check Configuration
```bash
# Verify credentials are loaded
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('CLIENT_ID:', os.getenv('GOOGLE_CLIENT_ID', 'NOT SET')[:20] + '...')
print('CLIENT_SECRET:', 'SET' if os.getenv('GOOGLE_CLIENT_SECRET') else 'NOT SET')
print('REDIRECT_URI:', os.getenv('REDIRECT_URI', 'http://127.0.0.1:5000/callback'))
"
```

### Step 2: Enable Debug Logging
The updated code now shows detailed errors. Run app with logging:

```bash
# Terminal 1: Start app with debug logging
export FLASK_ENV=development
export FLASK_DEBUG=1
export PYTHONUNBUFFERED=1
python app.py
```

```bash
# Terminal 2: Watch logs while testing
tail -f /tmp/flask_debug.log
```

### Step 3: Check Browser Console
1. Open browser Developer Tools (F12 → Network tab)
2. Click "Sign in with Google"
3. Watch the network requests
4. Right-click on the failed request to Google → Copy as cURL
5. Run the cURL command to see actual error from Google

### Step 4: Test Token Exchange Manually

```python
# Create test_oauth.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# You'll need to get an authorization code first
# Go to this URL in browser, authorize, and copy the 'code' param
auth_url = (
    "https://accounts.google.com/o/oauth2/v2/auth?"
    f"client_id={os.getenv('GOOGLE_CLIENT_ID')}"
    f"&redirect_uri=http://127.0.0.1:5000/callback"
    "&response_type=code"
    "&scope=openid email profile"
)
print("Visit this URL:")
print(auth_url)
print("\nPaste the code from redirect URL:")
code = input("Enter authorization code: ")

# Now test token exchange
response = requests.post(
    "https://oauth2.googleapis.com/token",
    data={
        "code": code,
        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
        "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
        "redirect_uri": "http://127.0.0.1:5000/callback",
        "grant_type": "authorization_code"
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
```

Run it:
```bash
python test_oauth.py
```

## Solution by Error Message

### "redirect_uri_mismatch"
```
→ Go to Google Console
→ Check Authorized redirect URIs
→ Update .env REDIRECT_URI to match exactly
→ Restart app
```

### "invalid_client"
```
→ Your client_id or client_secret is wrong
→ Regenerate credentials in Google Console
→ Update .env file
```

### "invalid_grant"
```
→ Authorization code already used, expired, or invalid
→ Clear cookies
→ Start login flow again
```

### "invalid_request"
```
→ Missing or malformed parameter
→ Check all required fields are present
→ Ensure proper URL encoding
```

## Google Console Configuration Checklist

```
[ ] Project is created
[ ] Google+ API is enabled
[ ] OAuth 2.0 Client ID is created
[ ] Client ID type is "Web application"
[ ] Authorized JavaScript origins includes: http://127.0.0.1 or http://localhost
[ ] Authorized redirect URIs includes EXACTLY: http://127.0.0.1:5000/callback
[ ] OAuth consent screen is configured (at least test app)
[ ] Email scope is included in consent screen
```

## Quick Fixes by Status Code

| Code | Meaning | Fix |
|------|---------|-----|
| 400 | Bad Request | Check redirect URI, credentials, parameters |
| 401 | Unauthorized | Invalid client_secret or credentials revoked |
| 403 | Forbidden | Scopes not granted, app not verified |
| 500 | Server Error | Temporary Google issue, try again later |

## Environment File Template

Create/update `.env.local`:
```bash
# Google OAuth (from Google Cloud Console)
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_key

# Must match Google Console Authorized redirect URIs exactly
REDIRECT_URI=http://127.0.0.1:5000/callback

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/interview_proai

# Flask
SECRET_KEY=your_random_secret_key_here
```

## Testing the Fix

1. **Start the app:**
   ```bash
   python app.py
   ```

2. **Open browser to:** `http://127.0.0.1:5000`

3. **Click "Sign in with Google"**

4. **Check the response:**
   - ✅ Success: Redirects to dashboard
   - ❌ Error: Shows detailed error message with debugging info

5. **If error, check:**
   - Terminal logs for detailed traceback
   - Browser Network tab for request/response details
   - Redirect URI matches Google Console

## Getting Help

If you're still stuck:

1. **Collect diagnostics:**
   ```bash
   # Full error output
   python app.py 2>&1 | tee oauth_debug.log
   ```

2. **Check Google's documentation:**
   - [OAuth 2.0 Implementation](https://developers.google.com/identity/protocols/oauth2)
   - [Error codes reference](https://developers.google.com/identity/protocols/oauth2#token-endpoint-response)

3. **Verify credentials are actually new:**
   - Delete your app's OAuth credentials
   - Create fresh ones
   - Wait 5-10 minutes for propagation
   - Update `.env` and restart
