"""
Database Schema Sync Utility — Adds OTP table and new User columns if missing
Supports --cloud flag to directly sync the live Clever Cloud production database.
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# If --cloud is specified, override DATABASE_URL with Clever Cloud credentials
if '--cloud' in sys.argv:
    CLOUD_DB = "mysql+pymysql://uxalmfjgjvtfjurr:6EWiN7hocZuoMxklRQoI@bkyprysysfkerjvkumqz-mysql.services.clever-cloud.com:3306/bkyprysysfkerjvkumqz?charset=utf8mb4"
    os.environ['DATABASE_URL'] = CLOUD_DB
    print("🌐 Targeting Live Clever Cloud Database...")

from app import create_app, db

app = create_app()

def sync_schema():
    with app.app_context():
        print(f"🔄 Syncing database schema on: {db.engine.url.host}...")
        
        # 1. Create any missing tables (like otp_verifications)
        db.create_all()
        print("✅ Tables verified (otp_verifications, users, accounts, etc.).")
        
        # 2. Add is_admin and is_verified columns to users if missing
        engine = db.engine
        with engine.connect() as conn:
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

        print("🎉 Database schema is 100% synchronized and up to date!")

if __name__ == '__main__':
    sync_schema()
