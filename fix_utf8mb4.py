import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

# Use your Clever Cloud connection details
DB_HOST = "bkyprysysfkerjvkumqz-mysql.services.clever-cloud.com"
DB_USER = "uxalmfjgjvtfjurr"
DB_PASS = "6EWiN7hocZuoMxklRQoI"
DB_NAME = "bkyprysysfkerjvkumqz"

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
