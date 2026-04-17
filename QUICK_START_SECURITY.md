# 🚀 QUICK START: Credentials Security Setup (5 Minutes)

**Just implemented credentials security, need to get running? Start here!**

---

## Option 1: Automated Setup (Recommended - 3 minutes)

```bash
# Run this once
bash setup-environment.sh

# Follow the prompts to enter:
# - Database host/port/credentials
# - Redis URL
# - Choose an AI backend
# - Google OAuth credentials

# Done! Your .env is set up and pre-commit hook is installed
```

---

## Option 2: Manual Setup (5 minutes)

```bash
# 1. Create .env from template
cp .env.example .env

# 2. Generate a secure SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Edit .env and add your values
nano .env
# Replace:
# - SECRET_KEY=<paste-generated-key>
# - DATABASE_URL=postgresql://user:pass@localhost:5432/interview_proai
# - REDIS_URL=redis://localhost:6379/0
# - GOOGLE_CLIENT_ID=<from Google Cloud Console>
# - GOOGLE_CLIENT_SECRET=<from Google Cloud Console>

# 4. Install git security hook
chmod +x .git-hooks/pre-commit-secrets
cp .git-hooks/pre-commit-secrets .git/hooks/pre-commit

# 5. Validate everything
python3 utils/validate_env.py
```

---

## ⚠️ CRITICAL: Handle Exposed Credentials

**Your Google OAuth secret is exposed in Git!**

See: `EXPOSED_CREDENTIALS_ACTION_REQUIRED.md` for detailed steps

**Quick version (15 minutes):**
1. Go to Google Cloud Console
2. Delete old OAuth client: `979257792760-65lvisp4b1klo9vdgvg61vva4bk5otc9`
3. Create new OAuth client
4. Update `.env` with new credentials
5. Remove `client_secret.json` from Git history

---

## 3. Start the App

```bash
python app.py
```

**You should see:**
```
🔐 Environment Validation Starting...

✅ Required variables for 'development' environment: OK
✅ No hardcoded secrets detected in source files
✅ AI backends available: ollama
✅ REDIS_URL: Configured

✅ Environment validation complete!

 * Serving Flask app 'app'
 * Running on http://127.0.0.1:5000
```

---

## 4. Test Everything Works

```bash
# In another terminal:
curl http://localhost:5000          # Should get homepage
curl http://127.0.0.1:5000/login    # Should get login page

# Test AI backend
python3 -c "from utils.ai_engine import generate_question; print(generate_question('Python'))"

# Should output an AI-generated question
```

---

## 5. Install Pre-commit Hook (Already Done!)

The pre-commit hook prevents accidentally committing secrets:

```bash
# Try to commit a fake secret - this should fail
echo "sk-test-secret" > test.txt
git add test.txt
git commit -m "test"  # ❌ BLOCKED by pre-commit hook!

# Remove the file and try again
rm test.txt
git add -A
git commit -m "cleanup"  # ✅ OK
```

---

## What's New?

**Files created for security:**
- `utils/validate_env.py` - Validates your environment
- `setup-environment.sh` - Automated .env setup
- `.git-hooks/pre-commit-secrets` - Prevents secret commits
- `CREDENTIALS_SECURITY.md` - Full security guide
- `EXPOSED_CREDENTIALS_ACTION_REQUIRED.md` - Incident response
- `ENVIRONMENT_TROUBLESHOOTING.md` - Debugging help

**Files modified:**
- `app.py` - Now validates environment at startup
- `.gitignore` - Enhanced with more secret patterns

---

## Common Issues? 

See the checklist below:

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: dotenv` | Run: `pip install python-dotenv` |
| `Missing required variables: SECRET_KEY` | Run: `cp .env.example .env` and fill in values |
| `Cannot connect to PostgreSQL` | Is PostgreSQL running? Check DATABASE_URL |
| `Cannot connect to Redis` | Is Redis running? Check REDIS_URL |
| `No AI backend configured` | Set at least one: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, OLLAMA_URL |

---

## Next Steps

1. ✅ **Done:** Secure environment setup (this guide)
2. ⏳ **Next:** Handle exposed credentials (`EXPOSED_CREDENTIALS_ACTION_REQUIRED.md`)
3. ⏳ **Then:** Input validation & testing (Tier 1/2)
4. ⏳ **Later:** Full security hardening (see roadmap)

---

## Quick Reference

**Environment validation:**
```bash
python3 utils/validate_env.py
```

**Re-setup environment:**
```bash
bash setup-environment.sh
```

**Manually edit environment:**
```bash
nano .env
```

**View environment variables:**
```bash
cat .env
# Be careful! This shows your secrets!
```

**Generate new SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Test database:**
```bash
python3 -c "from app import db; db.engine.connect(); print('✅ OK')"
```

**Test Redis:**
```bash
redis-cli -u $REDIS_URL ping
```

**Test AI backend:**
```bash
python3 -c "from utils.ai_engine import generate_question; print(generate_question('Python'))"
```

---

## Need Help?

- **How do I...?** → `CREDENTIALS_SECURITY.md`
- **Something's wrong** → `ENVIRONMENT_TROUBLESHOOTING.md`
- **Credentials exposed!** → `EXPOSED_CREDENTIALS_ACTION_REQUIRED.md`
- **Full implementation details** → `SECURITY_IMPLEMENTATION_SUMMARY.md`

---

**Time to implementation:** ~5 minutes
**Time to production ready:** ~25 minutes (including credential rotation)
**Status:** Ready to use! 🎉
