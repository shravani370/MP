# Render Deployment Guide

## Prerequisites
- PostgreSQL database (Render managed or external)
- Redis instance (Render managed or external)
- Google OAuth credentials (Client ID + Client Secret)
- SMTP credentials (for email notifications)

## Environment Variables for Render

Set these in your Render Service Settings → Environment:

```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=<generated-secure-key>
SECURE_COOKIES=True

# Database
DATABASE_URL=postgresql://user:password@hostname:5432/dbname
SQLALCHEMY_TRACK_MODIFICATIONS=False

# Redis (for sessions, caching, rate limiting)
REDIS_URL=redis://:password@hostname:port

# Google OAuth
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
REDIRECT_URI=https://your-domain.onrender.com/callback

# AI Backends (choose one or multiple)
OPENAI_API_KEY=<optional>
ANTHROPIC_API_KEY=<optional>
GOOGLE_API_KEY=<optional>

# Email Configuration
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=apikey
MAIL_PASSWORD=<sendgrid-api-key>
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# Application Settings
LOG_LEVEL=INFO
```

## Render Setup Steps

### 1. Create PostgreSQL Database
- Go to Render Dashboard → New → PostgreSQL
- Choose plan based on usage
- Note the DATABASE_URL (provided automatically)

### 2. Create Redis Instance
- Go to Render Dashboard → New → Redis
- Choose plan based on usage
- Note the REDIS_URL (provided automatically)

### 3. Create Web Service
- Go to Render Dashboard → New → Web Service
- Connect GitHub repo
- Build command: `pip install -r requirements.txt && alembic upgrade head`
- Start command: `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`
- Set all environment variables (see above)
- Configure auto-deploy from main/master branch

### 4. Run Database Migrations
After initial deployment:
```bash
# SSH into Render service or use CLI
render exec <service-name> -- alembic upgrade head
```

### 5. Configure Google OAuth
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Set Authorized Redirect URIs to: `https://your-domain.onrender.com/callback`
- Generate credentials (Client ID + Secret)
- Add to Render environment variables

## Critical Issues Fixed for Render

✅ **Rate Limiting**: Changed from memory backend to Redis  
✅ **File Storage**: Temporary files now use Redis with tempfile fallback  
✅ **Database Initialization**: Using Alembic migrations instead of db.create_all()  
✅ **REDIRECT_URI**: Validates production configuration and rejects if missing  
✅ **Sessions**: Using Redis backend (scales across multiple instances)  

## Troubleshooting

### "REDIRECT_URI environment variable is required in production"
**Solution**: Set `REDIRECT_URI=https://your-domain.onrender.com/callback` in Render environment

### Database Connection Errors
**Solution**: Ensure DATABASE_URL is set correctly with SSL:  
`postgresql://user:password@hostname:5432/db?sslmode=require`

### Redis Connection Errors
**Solution**: 
- Check REDIS_URL format: `redis://:password@hostname:port`
- Verify Redis instance is running
- Check firewall/security rules allow connection

### Google Auth 400 Error
**Solution**: 
- Ensure REDIRECT_URI exactly matches Google Console configuration
- Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are correct
- Check that protocol is HTTPS in production

### Sessions Lost Between Requests
**Solution**: Redis must be properly configured with SESSION_TYPE='redis'

## Monitoring

### Health Check
Render will automatically hit `/health` endpoint for health checks  
Response: `{"status": "ok"}`

### Logs
View real-time logs in Render Dashboard:
- Application logs
- Build logs
- Deployment history

### Error Tracking
Sentry is configured - errors will be automatically tracked (if SENTRY_DSN is set)

## Cost Optimization

- **PostgreSQL**: Start with Starter plan ($7/month), upgrade as needed
- **Redis**: Start with Starter plan ($10/month)
- **Web Service**: Pay-as-you-go, scales automatically
- **Bandwidth**: 100 GB free per month per service

## Production Checklist

- [ ] Set FLASK_ENV=production
- [ ] Generate strong SECRET_KEY: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] Enable SECURE_COOKIES=True
- [ ] Set REDIRECT_URI to your production domain
- [ ] Run Alembic migrations: `alembic upgrade head`
- [ ] Test Google OAuth flow end-to-end
- [ ] Configure email (SendGrid or equivalent)
- [ ] Set up proper logging/monitoring
- [ ] Enable auto-backups for PostgreSQL
- [ ] Configure CDN for static assets (optional)
