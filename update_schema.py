"""
Database Schema Sync Utility — Adds OTP table and new User columns if missing
"""
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

from app import create_app, db

app = create_app()

def sync_schema():
    with app.app_context():
        print("🔄 Syncing database schema...")
        
        # 1. Create any missing tables (like otp_verifications)
        db.create_all()
        print("✅ Checked tables: otp_verifications verified/created.")
        
        # 2. Add is_admin and is_verified columns to users if missing
        engine = db.engine
        with engine.connect() as conn:
            # Check users columns
            result = conn.execute(db.text("SHOW COLUMNS FROM users;"))
            cols = [row[0] for row in result.fetchall()]
            
            if 'is_admin' not in cols:
                print("Adding 'is_admin' column to users table...")
                conn.execute(db.text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;"))
                conn.commit()
                print("✅ Added 'is_admin' column.")
            else:
                print("ℹ️ 'is_admin' column already present.")

            if 'is_verified' not in cols:
                print("Adding 'is_verified' column to users table...")
                conn.execute(db.text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT TRUE;"))
                conn.commit()
                print("✅ Added 'is_verified' column.")
            else:
                print("ℹ️ 'is_verified' column already present.")

        print("🎉 Database schema is fully synced and up to date!")

if __name__ == '__main__':
    sync_schema()
