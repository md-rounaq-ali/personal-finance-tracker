"""
Database Reset Utility — Safely purges all registered users, transactions, and OTP records
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from app import create_app, db

app = create_app()

def wipe_all_users():
    with app.app_context():
        print("⚠️  Initiating complete database purge of all registered users...")
        
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
            # Always ensure foreign key checks are re-enabled
            try:
                db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1;"))
                db.session.commit()
            except Exception:
                pass
            print(f"❌ Error during database purge: {e}")

if __name__ == '__main__':
    wipe_all_users()
