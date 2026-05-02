# db_bridge.py
import mysql.connector
import sys
import os

# --- PATH FIX: Locate the 'database' folder ---
current_dir = os.path.dirname(os.path.abspath(__file__))
# Moves up to 'backend' and then into 'database'
database_dir = os.path.abspath(os.path.join(current_dir, "../../database"))

if database_dir not in sys.path:
    sys.path.append(database_dir)

# --- IMPORT FIX: Import the function from your specific db_config.py ---
try:
    from db_config import get_db_connection
except ImportError:
    print(f"❌ Critical Error: Could not find db_config.py in {database_dir}")
    sys.exit(1)

class DBBridge:
    def __init__(self):
        self.connection = None

    def connect(self):
        """Uses the get_db_connection() function from your config file."""
        try:
            # Calling the function exactly as defined in your file
            self.connection = get_db_connection()
            return self.connection
        except mysql.connector.Error as err:
            print(f"❌ Database Connection Error: {err}")
            return None

    def save_stylometric_features(self, doc_id, segment_idx, features):
        """Saves extracted stylometric features into the database."""
        conn = self.connect()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            # Note: Ensure you have created this table in 'sinhala_plagiarism_db'
            query = """
                INSERT INTO wsa_features 
                (doc_id, segment_idx, avg_sent_len, vocab_richness, punc_density) 
                VALUES (%s, %s, %s, %s, %s)
            """
            data = (
                doc_id, 
                segment_idx, 
                features['avg_sentence_length'], 
                features['vocabulary_richness'], 
                features['punctuation_density']
            )
            
            cursor.execute(query, data)
            conn.commit()
            cursor.close()
            return True
        except mysql.connector.Error as err:
            print(f"❌ Error saving to DB: {err}")
            return False
        finally:
            if conn and conn.is_connected():
                conn.close()

# --- TEST THE CONNECTION ---
if __name__ == "__main__":
    bridge = DBBridge()
    test_conn = bridge.connect()
    if test_conn:
        print("✅ SUCCESS: Successfully used get_db_connection() to link with MySQL!")
        test_conn.close()
    else:
        print("❌ FAILED: Still cannot connect. Check if MySQL is running.")