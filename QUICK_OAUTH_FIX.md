# QUICK FIX: OAuth 401 "invalid_client" Error

## 🔴 Problem
When you deployed your app and tried to login with Google, you got:
```
Access blocked: Authorisation error
Error 401: invalid_client
The OAuth client was not found.
```

## 🔵 Root Cause
Your OAuth client is configured for `http://127.0.0.1:5000/callback` (localhost), but your deployed app uses a different domain.

---

## ⚡ QUICK FIX (5 minutes)

### 1. What's Your Deployment Domain?
Write it here: `https://________________.com`

Examples:
- `https://interview-proai.herokuapp.com`
- `https://myapp.railway.app`
- `https://interview-proai.example.com`

### 2. Go to Google Cloud Console
- Link: https://console.cloud.google.com
- Select your project
- Go to: **APIs & Services** → **Credentials**
- Click on: Your OAuth 2.0 Client ID

### 3. Add Your Deployment URL
In the **"Authorized redirect URIs"** section, add:

```
https://YOUR-DEPLOYMENT-DOMAIN/callback
```

**Example:** `https://interview-proai.herokuapp.com/callback`

Keep the old one too:
```
http://127.0.0.1:5000/callback
```

So you should have BOTH:
- `http://127.0.0.1:5000/callback` (for local testing)
- `https://interview-proai.herokuapp.com/callback` (for production)

Click **SAVE**.

### 4. Update Your Deployment Environment
Set these environment variables on your deployment platform:

```
GOOGLE_CLIENT_ID=<CLIENT_ID>
GOOGLE_CLIENT_SECRET=<CLIENT_SECRET>
REDIRECT_URI=https://YOUR-DEPLOYMENT-DOMAIN/callback
```

**For Heroku:**
```bash
heroku config:set REDIRECT_URI=https://your-app.herokuapp.com/callback
heroku config:set GOOGLE_CLIENT_ID=<CLIENT_ID>
heroku config:set GOOGLE_CLIENT_SECRET=<CLIENT_SECRET>
```

**For Railway/Render:**
- Go to project settings
- Add Environment Variables tab
- Paste the 3 variables above

### 5. Test
1. Clear your browser cookies for that domain
2. Visit your deployed app
3. Click "Sign in with Google"
4. It should work now ✅

---

## 🔧 If It Still Doesn't Work

### Debug Step 1: Verify What Your App Is Using
Add this temporary route to `app.py`:

```python
@app.route("/debug-oauth")
def debug_oauth():
    import os
    return {
        "REDIRECT_URI": os.getenv("REDIRECT_URI"),
        "CLIENT_ID_FIRST_30_CHARS": os.getenv("GOOGLE_CLIENT_ID", "NOT SET")[:30],
        "CLIENT_SECRET_SET": "YES" if os.getenv("GOOGLE_CLIENT_SECRET") else "NO"
    }
```

Visit: `https://your-deployed-domain/debug-oauth`

Check if REDIRECT_URI matches your production domain.

### Debug Step 2: Check Browser Console
1. Right-click → Inspect → Network tab
2. Try login
3. Look for the OAuth request URL
4. Verify the `redirect_uri` parameter matches Google Cloud Console

### Debug Step 3: Common Mistakes
- ❌ Used `http://` instead of `https://`
- ❌ Added trailing slash: `/callback/` (should be `/callback`)
- ❌ Typo in domain name
- ❌ Environment variables not actually updated on deployment
- ❌ Old credentials still in cache (try incognito mode)

---

## 📝 Checklist
- [ ] Identified your deployment domain
- [ ] Logged into Google Cloud Console
- [ ] Added production domain to authorized redirect URIs
- [ ] Updated REDIRECT_URI in deployment environment variables
- [ ] Cleared browser cookies
- [ ] Tested login on deployed app
- [ ] Login works! ✅

---

## 📞 Still Stuck?
Tell me:
1. What platform are you deploying to? (Heroku, Railway, Docker, etc.)
2. What's your exact deployment domain?
3. Did you update the environment variables?
