import os
import sys

import mysql.connector


SUBMISSIONS_TABLE = "student_submissions"
TEXT_COLUMN = "text"
EMBEDDING_COLUMN = "embedding_blob"


current_dir = os.path.dirname(os.path.abspath(__file__))
database_dir = os.path.abspath(os.path.join(current_dir, "../../database"))

if database_dir not in sys.path:
    sys.path.append(database_dir)

try:
    from db_config import get_db_connection
except ImportError:
    print(f"Critical Error: Could not find db_config.py in {database_dir}")
    sys.exit(1)


class DBBridge:
    def __init__(self):
        self.init_db()

    def connect(self):
        try:
            return get_db_connection()
        except mysql.connector.Error as err:
            print(f"Database Connection Error: {err}")
            return None

    def init_db(self):
        """Keep WSA on the shared student_submissions table."""
        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {SUBMISSIONS_TABLE} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    {TEXT_COLUMN} LONGTEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """
            )

            columns = self._get_columns(cursor)

            if TEXT_COLUMN not in columns and "doc_text" in columns:
                cursor.execute(
                    f"ALTER TABLE {SUBMISSIONS_TABLE} "
                    f"ADD COLUMN {TEXT_COLUMN} LONGTEXT NULL"
                )
                cursor.execute(
                    f"UPDATE {SUBMISSIONS_TABLE} "
                    f"SET {TEXT_COLUMN} = doc_text "
                    f"WHERE {TEXT_COLUMN} IS NULL"
                )

            if EMBEDDING_COLUMN not in columns:
                cursor.execute(
                    f"ALTER TABLE {SUBMISSIONS_TABLE} "
                    f"ADD COLUMN {EMBEDDING_COLUMN} LONGBLOB NULL"
                )

            conn.commit()
            cursor.close()
        finally:
            conn.close()

    def _get_columns(self, cursor):
        cursor.execute(f"SHOW COLUMNS FROM {SUBMISSIONS_TABLE}")
        return {row[0] for row in cursor.fetchall()}

    def get_all_previous_submissions(self):
        conn = self.connect()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT id, {TEXT_COLUMN}, {EMBEDDING_COLUMN}
                FROM {SUBMISSIONS_TABLE}
                WHERE {TEXT_COLUMN} IS NOT NULL AND {TEXT_COLUMN} <> ''
                """
            )
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            print(f"Error fetching history: {e}")
            return []
        finally:
            conn.close()

    def save_new_submission(self, text, vec_blob):
        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {SUBMISSIONS_TABLE} ({TEXT_COLUMN}, {EMBEDDING_COLUMN})
                VALUES (%s, %s)
                """,
                (text, vec_blob),
            )
            conn.commit()
            cursor.close()
            print("DB: Document successfully archived.")
        except Exception as e:
            print(f"Error saving to DB: {e}")
        finally:
            conn.close()

    def update_submission_embedding(self, submission_id, vec_blob):
        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {SUBMISSIONS_TABLE}
                SET {EMBEDDING_COLUMN} = %s
                WHERE id = %s
                """,
                (vec_blob, submission_id),
            )
            conn.commit()
            cursor.close()
        except Exception as e:
            print(f"Error updating DB embedding: {e}")
        finally:
            conn.close()
