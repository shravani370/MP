# SQLite to SQLAlchemy Migration Checklist

## Status: Partially Complete ✅ 60%

This document tracks all the places in the codebase that need updating from SQLite to SQLAlchemy ORM.

---

## ✅ COMPLETED

### app.py
- [x] Imports updated (sqlalchemy, models)
- [x] Database initialization (SQLAlchemy)
- [x] Google OAuth callback (`/callback`)
- [x] Login route (`/login`)
- [x] Signup route (`/signup`)
- [x] Dashboard route (`/dashboard`)
- [x] Health check endpoint (`/health`)

---

## ⏳ REMAINING (Need Updates)

### app.py - Lines to Update

#### 1. Profile Update (Line 354)
**Current (SQLite):**
```python
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("UPDATE users SET name=? WHERE email=?", (name, email))
conn.commit()
conn.close()
```

**Should be (SQLAlchemy):**
```python
user = User.query.filter_by(email=email).first()
if user:
    user.name = name
    db.session.commit()
```

---

#### 2. Profile Stats Query (Lines 373-393)
**Current (SQLite):**
```python
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
    SELECT COUNT(*) as total_interviews,
    AVG((mcq_score + code_score) / 2.0) as average_score
    FROM screening_results WHERE email = ?
""", (email,))
stats = cursor.fetchone()
cursor.execute("""
    SELECT role, mcq_score, code_score, passed, created_at 
    FROM screening_results 
    WHERE email = ? ORDER BY created_at DESC LIMIT 10
""", (email,))
recent_interviews = cursor.fetchall()
conn.close()
```

**Should be (SQLAlchemy):**
```python
user = User.query.filter_by(email=email).first()
if user:
    results = ScreeningResult.query.filter_by(user_id=user.id).all()
    stats = {
        'total_interviews': len(results),
        'average_score': sum((r.mcq_score + r.code_score)/2 for r in results) / len(results) if results else 0
    }
    recent_interviews = ScreeningResult.query.filter_by(user_id=user.id).order_by(ScreeningResult.created_at.desc()).limit(10).all()
```

---

#### 3. Saved Jobs Query (Lines 996-1050)
**Current (SQLite):**
```python
conn = sqlite3.connect("users.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT * FROM saved_jobs WHERE email=? ORDER BY saved_at DESC", (email,))
jobs = [dict(job) for job in cursor.fetchall()]
conn.close()
```

**Should be (SQLAlchemy):**
```python
user = User.query.filter_by(email=email).first()
if user:
    jobs = SavedJob.query.filter_by(user_id=user.id).order_by(SavedJob.saved_at.desc()).all()
```

---

#### 4. Save/Delete Jobs (Lines 1032-1046)
**Current (SQLite):**
```python
cursor.execute(
    """INSERT INTO saved_jobs (email, job_id, title, company, location, url, saved_at)
       VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
    (email, job_id, title, company, location, url)
)
# And delete:
cursor.execute("DELETE FROM saved_jobs WHERE email=? AND job_id=?", (email, job_id))
```

**Should be (SQLAlchemy):**
```python
# Save
user = User.query.filter_by(email=email).first()
if user:
    job = SavedJob(
        user_id=user.id,
        email=email,
        job_id=job_id,
        title=title,
        company=company,
        location=location,
        url=url
    )
    db.session.add(job)
    db.session.commit()

# Delete
job = SavedJob.query.filter_by(user_id=user.id, job_id=job_id).first()
if job:
    db.session.delete(job)
    db.session.commit()
```

---

#### 5. Cover Letter Save (Lines ~1050-1100)
**Current (SQLite):**
```python
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute(
    """INSERT INTO cover_letters (email, name, role, company, job_desc, resume_text, letter)
       VALUES (?, ?, ?, ?, ?, ?, ?)""",
    (email, name, role, company, job_desc, resume_text, letter)
)
conn.commit()
conn.close()
```

**Should be (SQLAlchemy):**
```python
user = User.query.filter_by(email=email).first()
if user:
    cover_letter = CoverLetter(
        user_id=user.id,
        email=email,
        name=name,
        role=role,
        company=company,
        job_desc=job_desc,
        resume_text=resume_text,
        letter=letter
    )
    db.session.add(cover_letter)
    db.session.commit()
```

---

#### 6. Load Saved Cover Letters (Lines ~1100-1110)
**Current (SQLite):**
```python
conn = sqlite3.connect("users.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute(
    """SELECT id, name, role, company, created_at FROM cover_letters 
       WHERE email=? ORDER BY created_at DESC LIMIT 10""",
    (email,)
)
saved = [dict(row) for row in cursor.fetchall()]
conn.close()
```

**Should be (SQLAlchemy):**
```python
user = User.query.filter_by(email=email).first()
if user:
    saved = CoverLetter.query.filter_by(user_id=user.id).order_by(CoverLetter.created_at.desc()).limit(10).all()
```

---

### screening/screening_routes.py
**Status:** Needs review and update
- [ ] Check all database queries in screening routes
- [ ] Replace with SQLAlchemy ORM calls
- [ ] Import models from models.db

---

## 🔧 Quick Migration Template

```python
# BEFORE
from sqlite3 import connect
conn = connect("users.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM table WHERE col=?", (val,))
row = cursor.fetchone()
conn.close()

# AFTER
from models.db import db, YourModel
row = YourModel.query.filter_by(col=val).first()
```

---

## 🧪 Testing Checklist

After each update, test:
- [ ] User can login with email
- [ ] User can login with Google
- [ ] Dashboard loads and shows stats
- [ ] Profile editing works
- [ ] Saved jobs display correctly
- [ ] Can save/delete jobs
- [ ] Cover letter generation works
- [ ] Health check endpoint responds

---

## 🚀 Implementation Order

1. ✅ **Done (Priority 1):** Core auth routes (login, signup, callback)
2. **Next (Priority 2):** Profile and dashboard routes
3. **Next (Priority 3):** Job saving/loading
4. **Next (Priority 4):** Cover letters
5. **Next (Priority 5):** Screening routes (separate file)

---

## 📝 Notes

- Always include both email and user_id in denormalized queries for performance
- Use relationships (user.screening_results) for cleaner code
- Add try/except with db.session.rollback() for failed operations
- Test with multiple users to ensure no data leakage

---

## Command Reference

```bash
# Check for remaining sqlite3 references
grep -r "sqlite3\|\.execute\|cursor\|conn\." app.py screening/

# View current database schema
python -c "from models.db import db; print([table for table in db.metadata.tables])"

# Test database connection
python -c "from app import db; db.session.execute('SELECT 1'); print('✅ DB OK')"
```

---

**Completion Target:** 100% by end of next iteration  
**Estimated Effort:** 2-3 hours  
**Current Progress:** 60% ✅
