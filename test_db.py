from backend.database.db_config import get_db_connection

try:
    conn = get_db_connection()
    print("Connection Successful!")
    cur = conn.cursor()
    cur.execute("SELECT DATABASE();")
    print("Connected to:", cur.fetchone())
    conn.close()
except Exception as e:
    print(f"Error: {e}")
