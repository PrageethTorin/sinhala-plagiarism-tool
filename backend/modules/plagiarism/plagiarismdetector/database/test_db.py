from db_config import get_db_connection

conn = get_db_connection()

if conn:
    print("Connection object:", conn)
    conn.close()
    print("Database connection closed.")