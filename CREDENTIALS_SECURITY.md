# 🔐 Credentials & Security Management Guide

## IMMEDIATE ACTION REQUIRED ⚠️

Your `client_secret.json` containing Google OAuth credentials **is currently exposed in your Git repository**. This file should never be committed to version control.

### Step 1: Rotate Exposed Credentials (DO THIS NOW)

The exposed Google OAuth secret in your repository must be rotated immediately:

1. **Go to Google Cloud Console**
   ```
   https://console.cloud.google.com/
   → APIs & Services → Credentials
   → Find "Interview Pro AI" OAuth 2.0 Client
   ```

2. **Delete the exposed credential**
   - Click the trash icon next to the old client ID

3. **Create a new OAuth 2.0 Client**
   - Application type: Web application
   - Authorized JavaScript origins: `http://localhost:5000` (dev/staging)
   - Authorized redirect URIs: `http://localhost:5000/callback`
   - Copy the new credentials (save locally for now, we'll move to .env)

4. **Update your .env file** with new credentials:
   ```bash
   GOOGLE_CLIENT_ID=<your_new_client_id>
   GOOGLE_CLIENT_SECRET=<your_new_client_secret>
   ```

---

### Step 2: Remove Credentials from Git History

The exposed secret found its way into Git history. While it's rotated, remove it from the repo:

```bash
# Option A: Using BFG Repo-Cleaner (Recommended - fast, simple)
# 1. Install: brew install bfg
# 2. Clone a fresh copy if needed
# 3. Run: bfg --delete-files client_secret.json
# 4. Run: git reflog expire --expire=now --all && git gc --prune=now --aggressive
# 5. Run: git push origin --force --all

# Option B: Using git filter-branch (built-in, slower)
git filter-branch --tree-filter 'rm -f client_secret.json' HEAD
git push origin --force --all
```

**⚠️ Important**: Force pushing will rewrite history. Notify your team before doing this.

---

### Step 3: Secure .env File Setup

#### 3.1 Create your .env file
```bash
cp .env.example .env
```

#### 3.2 Edit .env with your actual credentials
```ini
# Development
FLASK_ENV=development
SECRET_KEY=generate-a-random-key-run-command-below
SECURE_COOKIES=False

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/interview_proai

# Redis (for sessions and caching)
REDIS_URL=redis://localhost:6379/0

# Google OAuth (use newly rotated credentials!)
GOOGLE_CLIENT_ID=your_new_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_new_client_secret

# AI Backends (choose at least one)
OPENAI_API_KEY=sk-... (optional)
ANTHROPIC_API_KEY=sk-ant-... (optional)
GOOGLE_API_KEY=AIzaSy... (optional)
OLLAMA_URL=http://localhost:11434/api/generate (optional)

# Email (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
```

#### 3.3 Generate a secure SECRET_KEY
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Output: kB7-4_Lp...
# Copy this and paste into .env as SECRET_KEY
```

---

### Step 4: Environment Validation at Startup

The application now validates your environment when it starts:

```bash
python app.py
```

You'll see output like:
```
🔐 Environment Validation Starting...

✅ Required variables for 'development' environment: OK
✅ No hardcoded secrets detected in source files
🤖 AI Backend Configuration:
   ✅ AI backends available: anthropic, ollama
📋 Optional Configuration:
   ✅ REDIS_URL: Configured
   ✅ EMAIL: Configured

✅ Environment validation complete!
```

---

## Production Deployment Checklist ✅

### Before deploying to production:

- [ ] **Rotate all credentials** (API keys, database passwords, OAuth secrets)
- [ ] **Generate strong SECRET_KEY**: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] **Set FLASK_ENV=production**
- [ ] **Set SECURE_COOKIES=True** (requires HTTPS)
- [ ] **Use PostgreSQL with SSL**: `postgresql://user:pass@host:port/db?sslmode=require`
- [ ] **Set REDIS_URL** to managed Redis (AWS ElastiCache, Heroku Redis, etc.)
- [ ] **Configure backup AI backends** (if primary is down)
- [ ] **Enable SENTRY_DSN** for error tracking
- [ ] **Set up log aggregation** (CloudWatch, DataDog, etc.)
- [ ] **Configure S3 for file uploads** (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, etc.)
- [ ] **Run validation**: app will fail to start if critical vars missing

### Production .env template:
```ini
FLASK_ENV=production
SECRET_KEY=<generate-with-secrets-module>
SECURE_COOKIES=True
DATABASE_URL=postgresql://user:pass@prod-host:5432/interview_proai?sslmode=require
REDIS_URL=redis://prod-host:6379/0
GOOGLE_CLIENT_ID=<from-google-cloud>
GOOGLE_CLIENT_SECRET=<from-google-cloud>
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
MAIL_SERVER=smtp.sendgrid.net
MAIL_USERNAME=apikey
MAIL_PASSWORD=SG.xxxxx
SENTRY_DSN=https://...@sentry.io/...
```

---

## Managing Secrets in Different Environments

### Development 
- Use `.env` file (already in .gitignore)
- Can use weaker credentials for testing
- Run validation to catch missing keys

### Staging
- Use environment variables or AWS Secrets Manager
- Use staging-specific API keys/databases
- Enable error tracking (Sentry)

### Production
- **NEVER** use .env files
- Use secrets management:
  - **AWS**: Secrets Manager or Parameter Store
  - **Heroku**: Config Vars
  - **Railway/Render**: Environment Variables
  - **Kubernetes**: Secrets
- All credentials should be separate/rotated regularly
- Enable comprehensive logging and monitoring

---

## Credential Rotation Schedule

- **API Keys**: Every 90 days, or immediately if compromised
- **Database Passwords**: Every 180 days
- **OAuth Secrets**: Immediately if ever exposed
- **SECRET_KEY**: After any suspected security incident
- **Service Account Keys**: Every 90 days

---

## Verification Commands

### Check that credentials are properly configured:
```bash
# Validate environment
python utils/validate_env.py

# Test database connection
python -c "from app import db; db.engine.connect(); print('✅ Database OK')"

# Test Redis connection
python -c "import redis; r = redis.from_url('$REDIS_URL'); r.ping(); print('✅ Redis OK')"

# Test AI backend
python -c "from utils.ai_engine import generate_question; print(generate_question('Python')[:50])"

# Test email (if configured)
python -c "from app import mail; mail.send_message('test', 'test@example.com', 'test'); print('✅ Email OK')"
```

---

## Best Practices Going Forward

✅ **DO:**
- Store all secrets in `.env` (development) or secrets manager (production)
- Rotate credentials regularly
- Use long, random API keys (use `secrets` module)
- Enable HTTPS for production
- Use database SSL connections
- Run validation at startup
- Keep credentials expiration dates in calendar

❌ **DON'T:**
- Commit `.env`, credentials, or API keys to Git
- Use default/example credentials in production
- Reuse credentials across environments
- Share credentials via email or chat
- Hardcode secrets in source code
- Use HTTP connections for production databases
- Store credentials in comments or documentation

---

## Troubleshooting

### "Missing required environment variables: SECRET_KEY"
→ Make sure you've created `.env` file and added all required variables

### "Cannot connect to PostgreSQL"
→ Check DATABASE_URL is correct, PostgreSQL is running, and credentials work

### "Cannot connect to Redis"
→ Check REDIS_URL is correct, Redis is running, and no authentication issues

### "No AI backend available"
→ Set at least one: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, or OLLAMA_URL

### "Something went wrong" on AI endpoints
→ Run validation and check that your chosen AI backend API key is correct

---

## Questions?

For more details on each service:
- **PostgreSQL**: See POSTGRES_SETUP.md
- **Redis**: See QUICK_START_CELERY.md
- **AI Backends**: See AI_INTEGRATION_SUMMARY.md
- **Deployment**: See ARCHITECTURE_AND_DEPLOYMENT.md
