"""
Database Reset Utility — Safely purges all registered users, transactions, and OTP records
Supports --cloud flag to purge the live Clever Cloud production database.
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# If --cloud is specified, override DATABASE_URL with Clever Cloud credentials
if '--cloud' in sys.argv:
    CLOUD_DB = os.environ.get('CLOUD_DATABASE_URL') or os.environ.get('DATABASE_URL')
    if not CLOUD_DB or 'localhost' in CLOUD_DB:
        print("❌ Error: CLOUD_DATABASE_URL environment variable is required to connect to cloud database.")
        sys.exit(1)
    os.environ['DATABASE_URL'] = CLOUD_DB
    print("🌐 Targeting Live Clever Cloud Database for purge...")

from app import create_app, db

app = create_app()

def wipe_all_users():
    with app.app_context():
        target_host = db.engine.url.host or 'localhost'
        print(f"⚠️  Initiating complete database purge on: {target_host}...")
        
        try:
            # Disable foreign key checks so child rows don't block deletion
            db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0;"))
            
            # Truncate / delete all dependent tables in clean order
            print("Purging transactions...")
            db.session.execute(db.text("DELETE FROM transactions;"))
            
            print("Purging budgets...")
            db.session.execute(db.text("DELETE FROM budgets;"))
            
            print("Purging accounts...")
            db.session.execute(db.text("DELETE FROM accounts;"))
            
            print("Purging categories...")
            db.session.execute(db.text("DELETE FROM categories;"))
            
            print("Purging OTP verifications...")
            db.session.execute(db.text("DELETE FROM otp_verifications;"))
            
            print("Purging users...")
            db.session.execute(db.text("DELETE FROM users;"))
            
            # Re-enable foreign key checks
            db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1;"))
            
            db.session.commit()
            print("✅ Successfully purged all users, transactions, and data!")
            print("Database is completely clean and ready for fresh registrations.")
        except Exception as e:
            db.session.rollback()
            try:
                db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1;"))
                db.session.commit()
            except Exception:
                pass
            print(f"❌ Error during database purge: {e}")

if __name__ == '__main__':
    wipe_all_users()
