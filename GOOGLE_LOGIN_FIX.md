# Google Login - NotNullViolation Fix

## Problem
Error: `psycopg2.errors.NotNullViolation: null value in column "email" of relation "users" violates not-null constraint`

This occurs when Google OAuth returns `NULL` for email or name fields.

## Root Causes

1. **Missing Email Scope** - Google OAuth not configured with `email` scope
2. **Insufficient Permissions** - Google app lacks scope approval from user
3. **Google Response Format** - Field names mismatch (using `given_name` instead of `name`)
4. **Redirect URI Mismatch** - OAuth callback not matching Google Console configuration

## Solution

### Step 1: Verify Google OAuth Configuration

Check your `.env` file has these variables:
```bash
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
REDIRECT_URI=http://127.0.0.1:5000/callback  # Must match Google Console
```

### Step 2: Fix Code (Already Applied ✅)

The `/callback` route now has:
- ✅ Validates email is present (required)
- ✅ Falls back to `given_name` if `name` missing
- ✅ Uses email username as last resort for name
- ✅ Better error logging for debugging
- ✅ HTTP status validation

### Step 3: Google Console Verification

Go to [Google Cloud Console](https://console.cloud.google.com):

1. Select your project
2. Go to **APIs & Services** → **Credentials**
3. Click your OAuth 2.0 Client ID
4. Verify **Authorized redirect URIs** includes: `http://127.0.0.1:5000/callback`
5. Go to **OAuth consent screen**
6. Verify **Scopes** include: `openid`, `email`, `profile`

### Step 4: Test the Fix

1. Clear browser cookies for localhost:5000
2. Start the app: `python app.py`
3. Try Google login again
4. Check logs for detailed error messages

## Detailed Error Messages

If login still fails, check the error response which now shows:

```
Failed to get email from Google account. Ensure email scope is granted.
```
This means Google app scopes need updating.

```
Failed to get access token: invalid_code
```
This means redirect URI doesn't match Google Console.

## Debug Mode

To enable detailed logging:

```bash
# In terminal before running app
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

Then check terminal logs when attempting Google login.

## Fallback Behavior

If `name` is missing, the code now:
1. Tries `name` field → ✅
2. Falls back to `given_name` → ✅
3. Falls back to email prefix (user@domain.com → "user") → ✅

## Database Migration

If you have existing test users with NULL values:

```sql
-- Option 1: Update NULL emails with a marker
UPDATE users SET email = 'migrated_' || id || '@invalid.local' 
WHERE email IS NULL;

-- Option 2: Delete test records
DELETE FROM users WHERE email IS NULL;
```

Then run: `alembic upgrade head`

## Success Indicators

✅ Email successfully extracted from Google response
✅ User created in database with non-null email
✅ Session established
✅ Redirected to homepage

## Contact Support

If issues persist after these steps, check:
1. Google Cloud Console OAuth settings
2. Application logs for detailed error
3. Browser Network tab (check Google auth URL params)
