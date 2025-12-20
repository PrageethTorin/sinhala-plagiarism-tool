import sys
import os
import mysql.connector

# --- IMPORT FIX ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../'))
sys.path.append(project_root)
# ------------------

from database.db_config import get_db_connection

class DBManager:
    # 1. Existing function (Keep this)
    def save_document(self, filename, content):
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO documents (filename, content) VALUES (%s, %s)"
        cursor.execute(sql, (filename, content))
        conn.commit()
        doc_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return doc_id

    # 2. Existing function (Keep this)
    def save_features(self, doc_id, features):
        conn = get_db_connection()
        cursor = conn.cursor()
        # Convert Dictionary to JSON string for the function_word_freq column
        import json
        func_freq_json = json.dumps(features.get('function_word_freq', {}), ensure_ascii=False)

        sql = """
            INSERT INTO stylometric_features 
            (document_id, avg_sentence_length, vocabulary_richness, function_word_freq, punctuation_density)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            doc_id,
            features['avg_sentence_length'],
            features['vocabulary_richness'],
            func_freq_json, 
            features['punctuation_density']
        ))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Success: Features saved for Document ID {doc_id}")

    # 3. NEW FUNCTION (For your new AI Logs)
    def save_plagiarism_log(self, text, result, features):
        conn = get_db_connection()
        cursor = conn.cursor()

        # Prepare short text snippet
        snippet = text[:100] + "..." if len(text) > 100 else text
        
        # Clean confidence score
        conf_value = float(result['confidence'].replace('%', ''))

        sql = """
        INSERT INTO plagiarism_logs 
        (text_snippet, prediction_label, confidence_score, avg_sentence_len, vocab_richness, punctuation_density)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        values = (
            snippet,
            result['prediction'],
            conf_value,
            features['avg_sentence_length'],
            features['vocabulary_richness'],
            features['punctuation_density']
        )

        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Database Success: Log saved to 'plagiarism_logs'")