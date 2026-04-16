# PostgreSQL Migration Setup Guide

## 🚀 Quick Start (5 minutes)

### Option A: Using Docker Compose (Recommended for Local Dev)

```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Start PostgreSQL + Redis
docker-compose up -d

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database
python -c "from app import db; db.create_all()"

# 5. Run the app
python app.py

# 6. Access at http://localhost:5000
```

### Option B: Manual PostgreSQL Installation

```bash
# macOS
brew install postgresql
brew services start postgresql
createdb interview_proai

# Linux (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
sudo -u postgres createdb interview_proai

# Windows
# Download from https://www.postgresql.org/download/windows/
```

Then update `.env`:
```env
DATABASE_URL=postgresql://localhost/interview_proai
```

---

## 📋 What Changed

### Before (SQLite)
```python
import sqlite3
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM users WHERE email=?", (email,))
user = cursor.fetchone()
conn.close()
```

### After (SQLAlchemy + PostgreSQL)
```python
from models.db import User
user = User.query.filter_by(email=email).first()
```

**Benefits:**
- ✅ Connection pooling (shared connections)
- ✅ Type safety (no SQL injection)
- ✅ Horizontal scaling (multiple servers)
- ✅ Migrations (version control for schema)
- ✅ Relationships (auto foreign keys)

---

## 🔧 Database Operations

### Initialize (first time)
```bash
python -c "from app import db; db.create_all()"
```

### View tables
```bash
# psql command line
psql -U postgres -d interview_proai

# Then in psql:
\dt                 # List all tables
\d users            # Show users table structure
SELECT * FROM users;  # Query data
```

### Reset database (⚠️ DELETE ALL DATA)
```bash
python -c "from app import db, app; app.app_context().push(); db.drop_all(); db.create_all()"
```

---

## 🔄 Using Alembic for Migrations

Alembic enables version control for database schema changes.

### Generate migration (after adding a column to model)

```python
# Example: Add phone_number column to User model
# models/db.py
class User(db.Model):
    # ... existing fields ...
    phone_number = db.Column(db.String(20))  # New column
```

Then:
```bash
# Generate migration file
alembic revision --autogenerate -m "Add phone_number to users"

# This creates: alembic/versions/XXX_add_phone_number_to_users.py
```

### Apply migration
```bash
alembic upgrade head
```

### View migration history
```bash
alembic history          # All migrations
alembic current          # Current version
alembic history -r20     # Last 20 migrations
```

### Rollback migration
```bash
alembic downgrade -1     # Go back one migration
alembic downgrade base   # Go to beginning
```

---

## 🐳 Docker Compose Reference

Start services:
```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f postgres   # PostgreSQL logs
docker-compose logs -f redis      # Redis logs
docker-compose logs -f app        # Flask app logs
```

Connect to PostgreSQL:
```bash
docker-compose exec postgres psql -U interview_user -d interview_proai
```

Stop services:
```bash
docker-compose down          # Keep volumes
docker-compose down -v       # Remove volumes (DELETE DATA!)
```

---

## 📊 Database Schema

### `users` table
```
id (PK)          | auto-increment
name             | string
email            | string, unique
password         | hashed string
auth_type        | 'email' or 'google'
created_at       | timestamp
```

### `screening_results` table
```
id (PK)          | auto-increment
user_id (FK)     | foreign key to users
email            | string (denormalized for queries)
role             | string (job role)
mcq_score        | integer
code_score       | integer
passed           | boolean
created_at       | timestamp
```

### `saved_jobs` table
```
id (PK)          | auto-increment
user_id (FK)     | foreign key to users
email            | string (denormalized)
job_id           | string (unique per user)
title            | string
company          | string
location         | string
url              | text
saved_at         | timestamp
(user_id, job_id) | unique constraint
```

### `cover_letters` table
```
id (PK)          | auto-increment
user_id (FK)     | foreign key to users
email            | string (denormalized)
name             | string
role             | string
company          | string
job_desc         | text
resume_text      | text
letter           | text
created_at       | timestamp
```

---

## 🔍 Troubleshooting

### "FATAL: Ident authentication failed"
```bash
# Use password authentication (local dev only)
DATABASE_URL=postgresql://postgres:password@localhost/interview_proai
```

### "database does not exist"
```bash
createdb interview_proai
# Or in Docker:
docker-compose exec postgres createdb -U interview_user interview_proai
```

### "table already exists" error during migration
```bash
# Rollback and try again
alembic downgrade base
# Then fix the migration script
alembic upgrade head
```

### Connection refused (PostgreSQL not running)
```bash
# Start PostgreSQL
brew services start postgresql
# Or Docker:
docker-compose up -d postgres
```

### SQLAlchemy errors about missing tables
```bash
# Recreate tables
python -c "from app import db; db.create_all()"
```

---

## 🚢 Production Deployment

### Use Managed PostgreSQL
- AWS RDS
- Heroku Postgres
- Railway
- Render
- DigitalOcean Managed Databases

### Environment Variables
```env
# Production
DATABASE_URL=postgresql://user:pass@prod-db.example.com:5432/db_name
SECURE_COOKIES=True
SECRET_KEY=very_long_random_string_...
```

### Connection Pooling
In production, use:
```python
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 20,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}
```

### Run Migrations
```bash
# Before deploying new code
alembic upgrade head

# In production container:
docker-compose exec app alembic upgrade head
```

---

## 📚 Next Steps

1. ✅ PostgreSQL + SQLAlchemy set up
2. ⏭️ Add Redis for sessions (5 min)
3. ⏭️ Add Celery for async tasks (20 min)
4. ⏭️ Add Sentry for error tracking (10 min)
5. ⏭️ Docker deployment (30 min)

See [roadmap.md](/memories/repo/interview-proai-roadmap.md) for full plan.

---

## Useful Commands Cheat Sheet

```bash
# Start dev server
python app.py

# Database commands
python -c "from app import db; db.create_all()"  # Create tables
python -c "from app import db, app; app.app_context().push(); db.drop_all()"  # Drop all

# Migrations (Alembic)
alembic upgrade head        # Apply pending migrations
alembic downgrade -1         # Rollback last migration
alembic revision --autogenerate -m "description"  # Generate migration

# PostgreSQL (psql)
psql -U postgres -d interview_proai
\dt                         # List tables
\d users                    # Show table structure
SELECT COUNT(*) FROM users;  # Count rows

# Docker
docker-compose up -d        # Start services
docker-compose down         # Stop services
docker-compose logs -f      # View logs
```

---

**Version:** 1.0  
**Updated:** April 2026  
**Status:** ✅ Production Ready
