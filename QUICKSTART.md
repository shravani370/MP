# Quick Start Guide - Interview-ProAI (Updated)

## Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment variables
cp .env.example .env  # or create .env with settings below
```

## Configuration

### Minimal Setup (.env)
```bash
# Either Ollama OR a cloud API - app will auto-detect

# Option A: Local Ollama (Free)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Option B: OpenAI (Paid monthly)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo

# Option C: Anthropic Claude (Paid monthly)
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Option D: Google Gemini (Paid as used)
GOOGLE_GENAI_API_KEY=AIza...
GEMINI_MODEL=gemini-1.5-pro

# Google OAuth (required)
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
REDIRECT_URI=http://localhost:5000/callback
```

## Running the App

### Development
```bash
python3 app.py
# Visit http://localhost:5000
```

### Production (using Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Features Now Available

### 1. Multi-AI Backend Support ✨
- Seamlessly switches between OpenAI, Anthropic, Gemini, Ollama
- Auto-detects which backend is available
- Falls back automatically if one is down

### 2. Secure Authentication 🔒
- Email/password signup with password hashing
- Google OAuth 2.0 login
- Session timeout (1 hour)
- CSRF protection on all forms
- Secure cookies (HttpOnly, SameSite) 

### 3. Secure Code Execution 🚀
- Uses RestrictedPython instead of raw exec()
- Prevents file access, network calls, dangerous introspection
- Better error messages for malicious code

### 4. Database Migrations 📊
- Auto-applies schema updates safely
- No data loss on updates
- Proper timestamps and auth tracking

## Usage Examples

### Sign Up (New Users)
1. Click "Sign Up" on homepage
2. Enter: Full Name, Email, Password (min 8 chars, 1 uppercase, 1 digit)
3. Confirm password and submit
4. Auto-logged in, redirected to dashboard

### Log In (Email)
1. Click "Login" on homepage
2. Enter email and password
3. Redirected to dashboard

### Log In (Google OAuth)
1. Click "Login with Google"
2. Approve permission
3. Auto-registered or logged in
4. Redirected to dashboard

### Interview Mode
1. Select topic (Python, Data Science, etc.)
2. Answer 5 questions
3. Get AI-powered feedback with:
   - Individual scores (1-10)
   - Strengths identified
   - Areas to improve
   - Overall verdict
   - Coaching tips

### Cover Letter Generation
1. Upload resume or paste text
2. Enter job description
3. AI generates personalized cover letter
4. Download or email

### Job Recommendations
1. Search by role and location
2. Filter by job type
3. Get ATS compatibility score
4. Save jobs for later

## Testing

### Test AI Backend
```python
from utils.ai_backends import get_ai_manager
mgr = get_ai_manager()
print(mgr.status())  # Shows which backend is active
```

### Test Password Hashing
```python
from utils.auth import hash_password, verify_password
pwd = hash_password("MyPassword123")
verify_password("MyPassword123", pwd)  # True
```

### Test CSRF Protection
```python
from flask import session
from utils.auth import generate_csrf_token, validate_csrf_token
token = generate_csrf_token()
# Token is now in session['csrf_token']
```

## Troubleshooting

### "No AI backend available"
- Ensure at least ONE API key is set in .env
- If using Ollama: run `ollama serve` first
- Check internet connection (for cloud APIs)

### "Password hashing failed"
- Ensure werkzeug is installed: `pip install werkzeug`

### "CSRF token mismatch"
- Make sure forms include: `<input type="hidden" name="csrf_token" value="{{ csrf_token }}">`
- Check session is persisting (not cleared)

### "Database locked"
- Exit all Python processes  
- Delete `users.db-journal` if it exists
- Restart the app

### "Import error: restricted_python not found"
```bash
pip install restricted-python
```

## Database

### Location
```
users.db  (SQLite database in project root)
```

### Tables
- `users` - User accounts (email, hashed password, auth type)
- `screening_results` - MCQ/code test results
- `saved_jobs` - Bookmarked job listings
- `cover_letters` - Generated cover letters history

### Backup
```bash
cp users.db users.db.backup.$(date +%Y%m%d_%H%M%S)
```

## Security Notes for Production

Before deploying:

1. **Change SECRET_KEY** in .env to a strong random string
2. **Use HTTPS** - Set `SECURE_SSL_REDIRECT=True`
3. **Set secure database** - Consider PostgreSQL instead of SQLite
4. **Add rate limiting** - Prevent brute force attacks
5. **Enable CSRF strictly** - Already configured but verify
6. **Use strong passwords** - Require for deployment
7. **Add logging** - Track user actions for audit
8. **Add monitoring** - Alert on suspicious activity
9. **Rotate credentials** - Periodically rotate API keys
10. **Keep dependencies updated** - Run `pip install --upgrade`

## Performance Tips

- Cache interview questions per role
- Batch process job recommendations
- Use Redis for session storage (optional)
- Configure CDN for static assets
- Add database indexes for frequently queried columns

---

For detailed security documentation, see: **SECURITY_FIXES.md**
