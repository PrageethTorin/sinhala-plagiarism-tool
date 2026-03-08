# backend/debug_lexical_db.py
import sys
import os
import mysql.connector

# Setup path to find db_config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'database')))
# If that fails, try the direct relative import if db_config is in backend/database
try:
    from database.db_config import get_db_connection
except ImportError:
    # Fallback if running from backend root
    from database.db_config import get_db_connection

def check_database():
    print("--- 🔍 INSPECTING DATABASE CONTENT ---")
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Check the first 5 rows to see if they are readable or just '????'
    print("\n1. First 5 Rows in Database:")
    cursor.execute("SELECT * FROM synonyms LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        print(f"   ID: {row[1]} | Word: {row[2]} | Synonym: {row[3]}")

    # 2. Search for the specific test word 'ආහාර'
    search_word = "ආහාර"
    print(f"\n2. Searching for '{search_word}'...")
    
    query = "SELECT * FROM synonyms WHERE word = %s OR synonym_word = %s"
    cursor.execute(query, (search_word, search_word))
    results = cursor.fetchall()
    
    if results:
        print(f"   ✅ FOUND IT! Linked to: {results}")
    else:
        print(f"   ❌ NOT FOUND. '{search_word}' is not in your database.")
        
    conn.close()

if __name__ == "__main__":
    check_database()