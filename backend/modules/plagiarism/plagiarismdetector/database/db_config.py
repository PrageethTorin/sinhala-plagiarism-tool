import mysql.connector

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Imalsha10",
            database="sinhala_plagiarism_db",
            charset="utf8mb4"
        )

        if conn.is_connected():
            print("✅ Database connected successfully!")
            return conn

    except mysql.connector.Error as err:
        print("❌ Database connection failed:", err)
        return None
