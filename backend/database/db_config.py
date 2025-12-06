# database/db_config.py
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",        # Change to your MySQL username
        password="root",# Change to your MySQL password
        database="sinhala_plagiarism_db",
        charset='utf8mb4'   # Critical for Sinhala font support
    )