# backend/add_synonyms.py
import sys
import os
import mysql.connector

# Connect to your database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'database')))
from database.db_config import get_db_connection

def add_new_words():
    print("--- 🎓 Teaching New Synonyms to Database ---")
    conn = get_db_connection()
    cursor = conn.cursor()

    # The new words we want to teach
    # Format: (Word, Synonym)
    new_data = [
        ("ගුරුතුමා", "ආචාර්යවරයා"),  # Teacher -> Lecturer
        ("සිසුන්ට", "ළමයින්ට"),      # Students -> Children
        ("පාඩම", "පාඩම")            # (Optional: reinforcing exact matches)
    ]

    try:
        query = "INSERT INTO synonyms (word, synonym_word) VALUES (%s, %s)"
        cursor.executemany(query, new_data)
        conn.commit()
        print(f"✅ Success! Added {cursor.rowcount} new pairs to the database.")
        
    except mysql.connector.Error as err:
        print(f"⚠️ Error: {err}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_new_words() 