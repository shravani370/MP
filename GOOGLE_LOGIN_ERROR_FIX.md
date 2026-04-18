# 🔧 Google Login Error - Schema Fix Guide

## Problem

When attempting Google Login, you received this error:

```
Google Login Error: (psycopg2.errors.UndefinedColumn) 
column users.password does not exist
```

## Root Cause

The `users` table in PostgreSQL was missing the `password` column, even though the SQLAlchemy model defined it. This happens when:

1. **Database migrations weren't run** - The schema wasn't synced from model definitions
2. **Partial migrations** - Some migrations ran but not all
3. **Manual database modifications** - Someone dropped or missed the column

## Solution

### ✅ Automatic Fix (On Next App Start)

The app now **automatically fixes missing columns** when it starts:

```bash
python app.py
# Output will show:
# ⚠️  Missing columns in 'users' table: {'password'}
# 💡 Attempting to add missing columns...
#    ✅ Added column: password
# ✅ Schema integrity check complete
```

### ✅ Manual Fix (If Needed)

Run the schema fix script:

```bash
python fix_database_schema.py
```

**Output:**
```
🔧 Database Schema Fix
📦 Database: postgresql://localhost/interview_proai...

✅ Query 'users' table
❌ Missing columns: {'password'}
📝 Adding missing columns...
   - Adding 'password'... ✅

✅ Schema fix complete!
```

### ✅ Alternative: Reset & Recreate (Development Only)

If you want a clean start:

```bash
# Drop all tables and recreate
python3 -c "from app import db, app; app.app_context().push(); db.drop_all(); db.create_all(); print('✅ Database reset complete')"
```

**⚠️ WARNING: This deletes all data!**

---

## Why This Happened

### The Model Defines It

In `models/db.py`, the `User` class defines:

```python
class User(db.Model):
    ...
    password = db.Column(db.String(255))  # ✅ Column defined
    ...
```

### But The Database Didn't Have It

When SQLAlchemy's `db.create_all()` runs, it **only creates missing tables and columns that don't exist**. If the table already existed without the column, the column wasn't automatically added.

### Timeline

1. **Initial setup** - `users` table created WITHOUT `password` column
2. **Later** - Model definition was updated to include `password` column
3. **app.py runs** - `db.create_all()` sees table exists, skips it
4. **Google Login** - Tries to query `password` column that doesn't exist → Error

---

## Prevention

### For Production

Use **Alembic migrations** to track schema changes:

```bash
# Create a migration
alembic revision --autogenerate -m "add password column"

# Run migrations
alembic upgrade head

# Check status
alembic current
```

### For Development

Just run the schema fix script or restart the app:

```bash
python fix_database_schema.py  # Manual fix
# OR
python app.py  # Auto-fixes on startup
```

---

## Testing It Works

Verify the column exists and queries work:

```bash
python3 << 'EOF'
from app import app, User

with app.app_context():
    # Test basic query
    user = User.query.first()
    print(f"✅ Query works: {user}")
    
    # Test new user
    new_user = User(
        name="Test",
        email="test@example.com",
        password="hashed_pwd",
        auth_type="google"
    )
    print(f"✅ Model works: {new_user.password}")
EOF
```

---

## Next Steps

1. ✅ **Automatic Fix Applied** - The app now handles this on startup
2. ✅ **Schema Verified** - Run test above to confirm
3. ✅ **Google Login** - Should now work without errors
4. 📝 **Use Migrations Going Forward** - For any future schema changes

---

## Troubleshooting

### Still Getting Column Error?

```bash
# Force immediate fix
python fix_database_schema.py

# Verify it worked
python3 -c "from app import app; app.app_context().push(); print(app.config['SQLALCHEMY_DATABASE_URI'])"
```

### PostgreSQL Won't Connect?

```bash
# Start PostgreSQL
brew services start postgresql@14

# Or use SQLite for development
export DATABASE_URL=sqlite:///interview_proai.db
python app.py
```

### Need to See All Columns?

```bash
python3 << 'EOF'
from app import app
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(app.db.engine)
    cols = inspector.get_columns('users')
    for col in cols:
        print(f"  - {col['name']}: {col['type']}")
EOF
```

---

## Related Files

- 📄 [fix_database_schema.py](fix_database_schema.py) - Schema fix utility
- 📄 [app.py](app.py) - Startup code with auto-fix
- 📄 [models/db.py](models/db.py) - SQLAlchemy models
- 📄 [alembic/](alembic/) - Database migrations

---

**Status**: ✅ Fixed | **Date**: 2026-04-18
