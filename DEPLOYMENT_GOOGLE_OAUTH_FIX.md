# Fix Google OAuth "invalid_client" Error on Deployment

## Problem
When deployed, you get: `Error 401: invalid_client - The OAuth client was not found`

**Root Cause:** Your OAuth credentials are configured for `http://127.0.0.1:5000/callback` (localhost), but your deployed app uses a different domain.

---

## Solution: 4 Steps to Fix

### Step 1: Determine Your Deployment Domain

What domain/URL are you using for your deployed app?
```
Examples:
- https://interview-proai.herokuapp.com
- https://interview-proai.example.com
- https://yourapp.railway.app
- etc.
```

**Your deployed domain:** ______________________

---

### Step 2: Create New OAuth 2.0 Credentials (Production)

**Go to Google Cloud Console:**
1. Open [console.cloud.google.com](https://console.cloud.google.com)
2. Select your project
3. Navigate to **APIs & Services** → **Credentials**
4. Click on your existing OAuth 2.0 Client ID (or create new one)
5. Update **Authorized redirect URIs:**

```
OLD (localhost only):
http://127.0.0.1:5000/callback

NEW (add both for flexibility):
http://127.0.0.1:5000/callback
https://YOUR-DEPLOYED-DOMAIN/callback
```

**Examples:**
```
✅ https://interview-proai.herokuapp.com/callback
✅ https://interview-proai.example.com/callback
✅ https://yourapp.railway.app/callback
```

6. **Save changes**
7. Download the OAuth credentials again

---

### Step 3: Update Your Environment Variables

#### For Local Development (.env file):
```bash
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET
REDIRECT_URI=http://127.0.0.1:5000/callback
```

#### For Production (Set in Deployment Platform):
```bash
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID           # Same as above
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET   # Same as above
REDIRECT_URI=https://YOUR-DEPLOYED-DOMAIN/callback   # PRODUCTION URL
```

**Where to set env vars:**

**🟡 Heroku:**
```bash
heroku config:set REDIRECT_URI=https://your-app.herokuapp.com/callback
```

**🟡 Railway/Render/Vercel:**
- Go to project settings → Environment Variables
- Add the three variables above

**🟡 Docker/VPS:**
- Update `.env` file or pass via `-e` flags

**🟡 AWS/Azure/GCP:**
- Use their secrets manager or environment variable settings

---

### Step 4: Test the Fix

1. **Clear browser cookies** (to clear old OAuth state):
   - DevTools → Application → Cookies → Delete all for your domain

2. **Visit your deployed app**

3. **Click "Sign in with Google"** and verify it works

---

## Verification Checklist

- [ ] OAuth credentials created/updated in Google Cloud Console
- [ ] Production redirect URI added to authorized URIs
- [ ] Environment variables updated on deployment platform
- [ ] REDIRECT_URI matches your production domain exactly
- [ ] Using HTTPS (not HTTP) for production URLs
- [ ] Browser cookies cleared

---

## Still Having Issues?

### Debug: Check What Your App Is Using
Add this temporary code to `app.py` to see what values are being loaded:

```python
@app.route("/debug/oauth-config")
def debug_oauth_config():
    import os
    return jsonify({
        "CLIENT_ID": os.getenv("GOOGLE_CLIENT_ID", "NOT SET")[:30] + "...",
        "CLIENT_SECRET": "SET" if os.getenv("GOOGLE_CLIENT_SECRET") else "NOT SET",
        "REDIRECT_URI": os.getenv("REDIRECT_URI", "NOT SET"),
    })
```

Visit `https://your-deployed-domain/debug/oauth-config` and verify the values.

### Common Mistakes
- ❌ Using `http://` instead of `https://` for production
- ❌ Adding trailing slash: `/callback/` (should be `/callback`)
- ❌ Wrong domain name (typo in environment variable)
- ❌ Old credentials still being cached (clear cookies!)
- ❌ Environment variables not actually set on deployment platform

### Request New OAuth Credentials (Nuclear Option)
If the above doesn't work:

1. Go to Google Cloud Console
2. Delete the old OAuth Client ID
3. Create a completely new one
4. Add only your production redirect URI
5. Copy new credentials
6. Update all environment variables
7. Test login flow again

---

## Code Reference

Your current OAuth code in `app.py`:

```python
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://127.0.0.1:5000/callback")

@app.route("/google-login")
def google_login():
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid email profile"
        "&access_type=offline"
        "&prompt=consent"
    )
    return redirect(auth_url)
```

This code is correct. Just make sure `REDIRECT_URI` env var is set correctly for your deployment!

---

## Need Help?

1. What platform are you deploying to? (Heroku, Railway, Docker, AWS, etc.)
2. What is your production domain?
3. Did you create new OAuth credentials or reuse existing ones?

Share these details if you're still stuck.
