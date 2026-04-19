#!/usr/bin/env python3
"""
Database Schema Fix Script
Ensures all required columns exist in the database tables
"""
import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError

def fix_database_schema():
    """Check and fix any missing columns in the database"""
    db_url = os.getenv('DATABASE_URL', 'sqlite:///interview_proai.db')
    
    print("🔧 Database Schema Fix")
    print(f"📦 Database: {db_url[:50]}...\n")
    
    try:
        # Create engine
        engine = create_engine(db_url)
        inspector = inspect(engine)
        
        # Check users table
        if 'users' not in inspector.get_table_names():
            print("❌ Table 'users' does not exist")
            print("💡 Run: python app.py (to create table)")
            return False
        
        # Get existing columns
        users_columns = {col['name'] for col in inspector.get_columns('users')}
        print(f"✅ Query 'users' table")
        print(f"   Existing columns: {sorted(users_columns)}\n")
        
        # Define required columns
        required_columns = {
            'id', 'name', 'email', 'password', 'auth_type', 'created_at'
        }
        
        # Find missing columns
        missing_columns = required_columns - users_columns
        
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}\n")
            print("📝 Adding missing columns...")
            
            with engine.connect() as conn:
                for col in sorted(missing_columns):
                    if col == 'id':
                        continue  # Should exist
                    elif col == 'name':
                        sql = "ALTER TABLE users ADD COLUMN name VARCHAR(255)"
                    elif col == 'email':
                        sql = "ALTER TABLE users ADD COLUMN email VARCHAR(255) NOT NULL UNIQUE"
                    elif col == 'password':
                        sql = "ALTER TABLE users ADD COLUMN password VARCHAR(255)"
                    elif col == 'auth_type':
                        sql = "ALTER TABLE users ADD COLUMN auth_type VARCHAR(50) DEFAULT 'email'"
                    elif col == 'created_at':
                        sql = "ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                    else:
                        continue
                    
                    try:
                        print(f"   - Adding '{col}'...", end=" ")
                        conn.execute(text(sql))
                        conn.commit()
                        print("✅")
                    except Exception as e:
                        # Column might already exist
                        print(f"ℹ️  ({str(e)[:40]}...)")
            
            print("\n✅ Schema fix complete!")
            return True
        else:
            print("✅ All required columns exist!")
            return True
            
    except OperationalError as e:
        print(f"❌ Database Connection Error:")
        print(f"   {e}\n")
        print("💡 Tips:")
        print("   - For PostgreSQL: brew services start postgresql@14")
        print("   - For SQLite: Just run the app (auto-creates)")
        print("   - OR set: export DATABASE_URL=sqlite:///interview_proai.db")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    success = fix_database_schema()
    sys.exit(0 if success else 1)
