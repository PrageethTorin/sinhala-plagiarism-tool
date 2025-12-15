import sys
import os
import mysql.connector

# --- IMPORT FIX ---
# This block adds the project root to Python's path so we can find 'database/db_config.py'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../'))
sys.path.append(project_root)
# ------------------

from database.db_config import get_db_connection

class DBManager:
    def save_document(self, filename, content):
        """Saves text to 'documents' table and returns the new ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = "INSERT INTO documents (filename, content) VALUES (%s, %s)"
        cursor.execute(sql, (filename, content))
        conn.commit()
        
        doc_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return doc_id

    def save_features(self, doc_id, features):
        """Saves analysis results to 'stylometric_features' table"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = """
            INSERT INTO stylometric_features 
            (document_id, avg_sentence_length, vocabulary_richness, function_word_freq, punctuation_density)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        cursor.execute(sql, (
            doc_id,
            features['avg_sentence_length'],
            features['vocabulary_richness'],
            features['function_word_freq'], 
            features['punctuation_density']
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Success: Data saved for Document ID {doc_id}")