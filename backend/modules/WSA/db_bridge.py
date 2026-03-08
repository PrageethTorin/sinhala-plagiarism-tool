# db_bridge.py
import mysql.connector
import sys
import os

# --- PATH FIX: Locate the 'database' folder ---
current_dir = os.path.dirname(os.path.abspath(__file__))
database_dir = os.path.abspath(os.path.join(current_dir, "../../database"))

if database_dir not in sys.path:
    sys.path.append(database_dir)

try:
    from db_config import get_db_connection
except ImportError:
    print(f"❌ Critical Error: Could not find db_config.py in {database_dir}")
    sys.exit(1)

class DBBridge:
    def __init__(self):
        self.init_db()

    def connect(self):
        """Uses the get_db_connection() function from your config file."""
        try:
            return get_db_connection()
        except mysql.connector.Error as err:
            print(f"❌ Database Connection Error: {err}")
            return None

    def init_db(self):
        """Ensures the student_submissions table exists with Sinhala support."""
        conn = self.connect()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS student_submissions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    doc_text LONGTEXT NOT NULL,
                    embedding_blob LONGBLOB NOT NULL,
                    submission_date DATETIME DEFAULT CURRENT_TIMESTAMP
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """)
            conn.commit()
            cursor.close()
        finally:
            conn.close()

    def get_all_previous_submissions(self):
        """FIXED: Added this method to retrieve history for collusion checks."""
        conn = self.connect()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, doc_text, embedding_blob FROM student_submissions")
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            print(f"❌ Error fetching history: {e}")
            return []
        finally:
            conn.close()

    def save_new_submission(self, text, vec_blob):
        """FIXED: Added this method to archive new unique documents."""
        conn = self.connect()
        if not conn: return
        try:
            cursor = conn.cursor()
            query = "INSERT INTO student_submissions (doc_text, embedding_blob) VALUES (%s, %s)"
            cursor.execute(query, (text, vec_blob))
            conn.commit()
            cursor.close()
            print("✅ DB: Document successfully archived.")
        except Exception as e:
            print(f"❌ Error saving to DB: {e}")
        finally:
            conn.close()