import mysql.connector

def get_db_connection():
    try:
        conn = mysql.connector.connect(
        host="localhost",
        user="root",        # Change to your MySQL username
        password="root",# Change to your MySQL password
        database="sinhala_plagiarism_db",
        charset='utf8mb4'   # Critical for Sinhala font support.
        )

        if conn.is_connected():
            print("✅ Database connected successfully!")
            return conn

    except mysql.connector.Error as err:
        print("❌ Database connection failed:", err)
        return None
