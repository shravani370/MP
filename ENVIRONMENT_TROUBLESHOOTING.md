# 🔍 Environment & Credentials Troubleshooting Guide

## Validation Failed at Startup?

If you see errors when running `python app.py`, check these in order:

### Error: "Missing required environment variables: X"

**Solution:**
1. Create `.env` file: `cp .env.example .env`
2. Open `.env` and fill in the missing variable
3. Make sure the variable is NOT commented out
4. Restart: `python app.py`

**Common missing variables:**
- `SECRET_KEY` - Generate: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- `DATABASE_URL` - Format: `postgresql://user:pass@host:port/dbname`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` - Get from Google Cloud Console

---

### Error: "Using default/development SECRET_KEY in production"

**Cause:** Your SECRET_KEY is set to the development default value.

**Solution:**
1. Generate a new secure key:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
2. Update your `.env`:
   ```ini
   SECRET_KEY=<paste-generated-key-here>
   ```

---

### Error: "DATABASE_URL uses unencrypted connection"

**Cause:** Your PostgreSQL connection doesn't use SSL/TLS encryption.

**Solution:**
1. For **development** (localhost): You can ignore this warning
2. For **production**: Update DATABASE_URL:
   ```ini
   # Before (unsafe)
   DATABASE_URL=postgresql://user:pass@remote-host:5432/db
   
   # After (secure)
   DATABASE_URL=postgresql://user:pass@remote-host:5432/db?sslmode=require
   ```
3. If using RDS/Heroku/managed database, SSL is usually built-in. Just add `?sslmode=require`

---

### Error: "No AI backend configured"

**Cause:** None of these are set: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, OLLAMA_URL

**Solution:** Add at least ONE:

**Option 1: Local Ollama (FREE, recommended for dev)**
```bash
# 1. Install Ollama from: https://ollama.ai
# 2. Run: ollama serve
# 3. In another terminal: ollama pull llama2
# 4. Add to .env:
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama2
```

**Option 2: OpenAI (paid)**
```bash
# 1. Get key from: https://platform.openai.com/account/api-keys
# 2. Add to .env:
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo
```

**Option 3: Anthropic Claude (paid)**
```bash
# 1. Get key from: https://console.anthropic.com/
# 2. Add to .env:
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-haiku-20240307
```

**Option 4: Google Gemini (paid)**
```bash
# 1. Get key from: https://aistudio.google.com/app/apikey
# 2. Add to .env:
GOOGLE_API_KEY=AIzaSy...
GOOGLE_MODEL=gemini-1.5-flash
```

---

### Error: "Cannot connect to PostgreSQL"

**Solution:**

1. **Verify PostgreSQL is running:**
   ```bash
   # macOS with Homebrew
   brew services list | grep postgres
   
   # Docker
   docker ps | grep postgres
   
   # Linux
   sudo systemctl status postgresql
   ```

2. **Check DATABASE_URL is correct:**
   ```bash
   # Should be format: postgresql://user:pass@host:port/dbname
   echo $DATABASE_URL
   ```

3. **Test connection manually:**
   ```bash
   psql postgresql://user:pass@localhost:5432/interview_proai
   ```

4. **Verify credentials:**
   - Are username/password correct?
   - Does the database exist? → `createdb interview_proai`
   - Is the user created? → `createuser interview_user`

5. **Check firewall/networking:**
   - If using remote database, can you reach it? → `nc -zv host 5432`
   - Are security groups allowing traffic?

---

### Error: "Cannot connect to Redis"

**Solution:**

1. **Verify Redis is running:**
   ```bash
   # macOS with Homebrew
   brew services list | grep redis
   
   # Docker
   docker ps | grep redis
   
   # Linux
   sudo systemctl status redis-server
   ```

2. **Check REDIS_URL:**
   ```bash
   echo $REDIS_URL
   # Should be format: redis://host:port/db (usually redis://localhost:6379/0)
   ```

3. **Test connection:**
   ```bash
   redis-cli -u $REDIS_URL ping
   # Should return: PONG
   ```

4. **If not installed, install Redis:**
   ```bash
   # macOS
   brew install redis
   brew services start redis
   
   # Docker
   docker run -d -p 6379:6379 redis:latest
   
   # Linux
   sudo apt install redis-server
   sudo systemctl start redis-server
   ```

---

### Warning: "SECURE_COOKIES not explicitly set in production"

**Cause:** In production, secure session cookies should be enabled.

**Solution:**
1. Add to `.env`:
   ```ini
   SECURE_COOKIES=True
   ```
   
2. **Important:** This requires HTTPS. You MUST have:
   - Valid SSL certificate
   - Flask/Gunicorn configured for HTTPS
   - Reverse proxy (nginx/Apache) handling HTTPS

3. If HTTPS not available yet, you can keep `False` during dev/testing, but enable before going live.

---

### Warning: "Email not configured"

**Cause:** Email notifications are disabled.

**Solution (optional):** To enable email features, add to `.env`:

```ini
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password  # NOT your regular password! Use app-specific password
MAIL_DEFAULT_SENDER=noreply@interview-proai.com
```

**For Gmail:**
1. Enable 2-factor authentication
2. Go to: https://myaccount.google.com/apppasswords
3. Select "Mail" and "Windows Computer" (or just create for app)
4. Copy the generated password
5. Use that password above (not your actual Gmail password)

---

### "SECURITY_FIXES.md or CREDENTIALS_SECURITY.md not found"

These are documentation files. They're created as part of this security setup. If you don't see them, that's OK - the important things are:
- `.env` file with your secrets
- `utils/validate_env.py` for validation
- Git pre-commit hook for safety

---

## Quick Verification Checklist ✅

Run these commands to verify everything is working:

```bash
# 1. Environment variables loaded
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ .env loaded' if os.getenv('SECRET_KEY') else '❌ .env not loaded')"

# 2. Database connectivity
python3 -c "from app import db; db.engine.connect(); print('✅ Database connected')"

# 3. Redis connectivity
python3 -c "import redis; r = redis.from_url('redis://localhost:6379/0'); r.ping(); print('✅ Redis connected')"

# 4. AI backend available
python3 -c "from utils.ai_engine import generate_question; print('✅ AI backend available')"

# 5. Environment validation passes
python3 utils/validate_env.py

# 6. App starts without errors
python3 app.py
```

---

## Production Deployment Verification

Before deploying to production, verify:

```bash
# 1. All secrets are in environment (not in code)
git grep -i "sk-" -- "*.py" | grep -v ".env" | grep -v "validate_env"
# Should be empty!

# 2. SECRET_KEY is strong and production-ready
python3 -c "import os; key = os.getenv('SECRET_KEY'); print(f'Length: {len(key)}'); print(f'Strong: {len(key) >= 32}')"

# 3. Database uses SSL
python3 -c "import os; print(os.getenv('DATABASE_URL')); print('⚠️ No SSL!' if 'sslmode' not in os.getenv('DATABASE_URL', '') else '✅ SSL enabled')"

# 4. SECURE_COOKIES enabled
python3 -c "import os; print('✅ SECURE_COOKIES enabled' if os.getenv('SECURE_COOKIES', '').lower() == 'true' else '⚠️ SECURE_COOKIES not enabled')"

# 5. Flask set to production
python3 -c "import os; print('✅ Production mode' if os.getenv('FLASK_ENV') == 'production' else '⚠️ Not production mode')"
```

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named '.env'` | `.env` not created | `cp .env.example .env` |
| `KeyError: 'SECRET_KEY'` | SECRET_KEY not in .env | Add `SECRET_KEY=<generated-key>` |
| `OperationalError: FATAL: role "postgres" does not exist` | PostgreSQL user not created | Run `createuser interview_user` |
| `ConnectionRefusedError: [Errno 61] Connection refused` | Service not running | Start PostgreSQL/Redis/Ollama |
| `API request failed: 401 Unauthorized` | Invalid API key | Check OPENAI_API_KEY/ANTHROPIC_API_KEY format |
| `redis.ConnectionError: Connection refused` | Redis not running | `redis-cli ping` or start Redis |

---

## When to Rotate Credentials

- **API Keys**: Every 90 days OR immediately if exposed
- **Database passwords**: Every 180 days
- **OAuth secrets**: Immediately if exposed
- **SECRET_KEY**: After any security incident
- **Session tokens**: Automatically managed by Flask

---

## Need More Help?

1. **General setup**: See [CREDENTIALS_SECURITY.md](CREDENTIALS_SECURITY.md)
2. **Database issues**: See [POSTGRES_SETUP.md](POSTGRES_SETUP.md)
3. **AI integration**: See [AI_INTEGRATION_SUMMARY.md](AI_INTEGRATION_SUMMARY.md)
4. **Deployment**: See [ARCHITECTURE_AND_DEPLOYMENT.md](ARCHITECTURE_AND_DEPLOYMENT.md)
5. **Celery/async**: See [QUICK_START_CELERY.md](QUICK_START_CELERY.md)

---

## Reporting Security Issues

If you discover a security vulnerability:
1. **DO NOT** commit it or push it
2. **DO** report it safely to your team lead
3. **DO** rotate any exposed credentials immediately
4. **DO** run `git filter-branch` or `bfg` to remove from history
5. **DO** send a force push after cleaning history

Remember: **Security is everyone's responsibility!** 🔐
