import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

# Database connection details from environment or cloud
database_url = os.environ.get('DATABASE_URL', '')
if 'mysql' in database_url and '@' in database_url:
    # Parse standard connection string
    # mysql+pymysql://user:password@host:port/dbname
    from urllib.parse import urlparse
    parsed = urlparse(database_url.replace('mysql+pymysql://', 'mysql://'))
    DB_HOST = parsed.hostname
    DB_USER = parsed.username
    DB_PASS = parsed.password
    DB_NAME = parsed.path.lstrip('/')
    DB_PORT = parsed.port or 3306
else:
    DB_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    DB_USER = os.environ.get('MYSQL_USER', 'root')
    DB_PASS = os.environ.get('MYSQL_PASSWORD', '')
    DB_NAME = os.environ.get('MYSQL_DB', 'personal_finance_tracker')
    DB_PORT = int(os.environ.get('MYSQL_PORT', 3306))

print("🔄 Connecting to Clever Cloud database to convert to utf8mb4...")

try:
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        charset='utf8mb4'
    )
    
    with connection.cursor() as cursor:
        # 1. Alter Database
        print("1️⃣ Converting database default character set to utf8mb4...")
        cursor.execute(f"ALTER DATABASE {DB_NAME} CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;")
        
        # 2. Get all tables
        cursor.execute("SHOW TABLES;")
        tables = [row[0] for row in cursor.fetchall()]
        
        # 3. Alter each table
        print(f"2️⃣ Converting {len(tables)} tables to utf8mb4...")
        for table in tables:
            print(f"   - Converting table: {table}")
            cursor.execute(f"ALTER TABLE `{table}` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            
    connection.commit()
    print("✅ Database and all tables successfully converted to utf8mb4! Emojis are now fully supported.")
    
except Exception as e:
    print(f"❌ Error converting database: {e}")
finally:
    if 'connection' in locals() and connection.open:
        connection.close()
