# PostgreSQL + SQLAlchemy Migration Guide

## Step 1: Install & Run PostgreSQL

### macOS
```bash
brew install postgresql
brew services start postgresql
createdb interview_proai
```

### Verify PostgreSQL is running
```bash
psql -U postgres -d interview_proai -c "SELECT 1;"
```

---

## Step 2: Update `.env` file

Add or update these variables:
```env
# Database
DATABASE_URL=postgresql://localhost/interview_proai

# AI Services (existing)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
OLLAMA_URL=http://localhost:11434/api/generate

# Security
SECRET_KEY=your_dev_secret_key_here
SECURE_COOKIES=False  # True in production only

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
REDIRECT_URI=http://127.0.0.1:5000/callback
```

---

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `sqlalchemy==2.0.23`
- `psycopg2-binary==2.9.9` (PostgreSQL driver)
- `alembic==1.12.1` (Migration tool)
- `Flask-SQLAlchemy==3.1.1` (Flask integration)

---

## Step 4: Initialize Database with Migrations

### First time setup:
```bash
# Create tables from models
python -c "from app import db, app; db.create_all()"
```

### For subsequent changes:
```bash
# Auto-generate migration based on model changes
alembic revision --autogenerate -m "description of change"

# Apply migrations
alembic upgrade head

# View migration status
alembic current
alembic history
```

---

## Step 5: Migrate Data (if you have existing SQLite data)

Use this script ONCE to migrate from SQLite → PostgreSQL:

```bash
python scripts/migrate_sqlite_to_postgres.py
```

---

## Step 6: Docker Compose for Local Development

Start PostgreSQL without manual setup:
```bash
docker-compose up -d
```

This starts:
- PostgreSQL on `localhost:5432`
- Creates database automatically
- Persists data in `postgres_data/` volume

---

## Key Changes in Code

### Before (SQLite):
```python
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM users WHERE email=?", (email,))
user = cursor.fetchone()
conn.close()
```

### After (SQLAlchemy):
```python
from models.db import db, User

user = User.query.filter_by(email=email).first()
# Or with async later:
# user = await db.session.execute(select(User).filter_by(email=email))
```

---

## Command Reference

```bash
# Start dev server with SQLAlchemy
python app.py

# Create tables (if not using migrations)
python -c "from app import db; db.create_all()"

# Run migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Generate new migration
alembic revision --autogenerate -m "Add user.phone_number"
```

---

## Troubleshooting

### "FATAL: Ident authentication failed"
```bash
# Edit PostgreSQL connection (local dev only)
# Or use password:
DATABASE_URL=postgresql://postgres:password@localhost/interview_proai
```

### "database does not exist"
```bash
createdb interview_proai
```

### "table already exists" error
Drop and recreate:
```bash
python -c "from app import db, app; db.drop_all(); db.create_all()"
```

### Check migrations
```bash
alembic current          # Current migration
alembic history          # All migrations
alembic history -r20     # Last 20 migrations
```

---

## Benefits After Migration

✅ **Connection Pooling**: Share DB connections across requests
✅ **Type Safety**: SQLAlchemy ORM prevents SQL injection  
✅ **Migrations**: Version control database schema
✅ **Scalability**: Can run multiple Flask instances against PostgreSQL
✅ **Relationships**: Foreign keys automatically validated
✅ **Querying**: Readable ORM queries instead of raw SQL

---

## Next Steps

After PostgreSQL + SQLAlchemy is working:
1. Add Redis for sessions (5 min change)
2. Add Celery for async tasks (remove blocking AI calls)
3. Add error tracking (Sentry)
4. Containerize with Docker
