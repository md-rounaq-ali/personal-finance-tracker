"""
FinTrack User Inspector Utility
Usage:
  python check_users.py         (Inspects Local MySQL Database)
  python check_users.py --cloud (Inspects Live Cloud MySQL Database on Clever Cloud)
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# If --cloud is passed, target Clever Cloud production database
if '--cloud' in sys.argv:
    CLOUD_DB = "mysql+pymysql://uxalmfjgjvtfjurr:6EWiN7hocZuoMxklRQoI@bkyprysysfkerjvkumqz-mysql.services.clever-cloud.com:3306/bkyprysysfkerjvkumqz?charset=utf8mb4"
    os.environ['DATABASE_URL'] = CLOUD_DB
    print("\n🌐 Connecting to LIVE CLOUD DATABASE (Clever Cloud MySQL)...")
else:
    print("\n💻 Connecting to LOCAL DATABASE (MySQL Localhost)...")

from app import create_app, db
from app.models import User, Account, Transaction

app = create_app()

def inspect_users():
    with app.app_context():
        users = User.query.order_by(User.id.asc()).all()
        print("=" * 80)
        print(f"{'ID':<4} | {'EMAIL':<32} | {'USERNAME':<16} | {'ADMIN':<7} | {'VERIFIED':<8}")
        print("=" * 80)
        if not users:
            print("  No users found in this database.")
        for u in users:
            admin_badge = "YES 👑" if u.is_admin else "NO"
            verified_badge = "YES ✅" if u.is_verified else "NO ❌"
            print(f"{u.id:<4} | {u.email:<32} | {u.username:<16} | {admin_badge:<7} | {verified_badge:<8}")
        print("=" * 80)
        print(f"Total Users Registered: {len(users)}\n")

if __name__ == '__main__':
    inspect_users()
