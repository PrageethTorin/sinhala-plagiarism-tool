# test_db.py
from database.db_config import get_db_connection
import mysql.connector

try:
    print("Attempting to connect...")
    
    # 1. Try to get the connection
    conn = get_db_connection()
    
    # 2. If we get here, the login worked. Now let's check the database info.
    if conn.is_connected():
        db_info = conn.get_server_info()
        print(f"✅ SUCCESS! Connected to MySQL Server version {db_info}")
        
        # 3. Let's check if your table exists
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        
        print(f"📂 Database '{conn.database}' contains these tables:")
        for table in tables:
            print(f" - {table[0]}")
            
        cursor.close()
        conn.close()
        print("\nConnection closed. You are ready to go!")
        
except mysql.connector.Error as err:
    # This block runs if something goes wrong
    print(f"\n❌ ERROR: Could not connect.")
    print(f"Reason: {err}")
    
except ImportError:
    print("\n❌ ERROR: Python cannot find your 'database' folder.")
    print("Make sure you are running this script from the root 'SinhalaParaphraseProject' folder.")