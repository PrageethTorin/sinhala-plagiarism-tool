import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root", # Ensure this is correct!
        database="sinhala_plagiarism_db"
    )
    print("Connection Successful!")
    cur = conn.cursor()
    cur.execute("SELECT DATABASE();")
    print("Connected to:", cur.fetchone())
    conn.close()
except Exception as e:
    print(f"Error: {e}")