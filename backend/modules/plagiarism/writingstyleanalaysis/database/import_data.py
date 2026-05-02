# database/import_data.py
import mysql.connector
import pandas as pd
import os
import sys

# Add the parent folder to the path so we can import db_config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_config import get_db_connection

def import_csv_to_db():
    print("🚀 Starting Data Import...")
    
    # 1. Connect to Database
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("✅ Connected to database.")
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return

    # 2. Load the CSV File
    # We use 'utf-8-sig' to handle potential BOM characters from Excel/Notepad
    file_path = 'data/Dataset(synonyms ).csv'
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        print("Make sure your CSV is in the 'data' folder.")
        return

    try:
        # Load data using pandas
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        # Clean column names (remove extra spaces)
        df.columns = [c.strip() for c in df.columns]
        
        print(f"📄 Found {len(df)} rows in CSV.")
        print(f"   Columns: {list(df.columns)}")

    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return

    # 3. Insert Data into MySQL
    inserted_count = 0
    errors = 0
    
    # SQL Query
    sql = "INSERT INTO synonyms (csv_id, word, synonym_word) VALUES (%s, %s, %s)"

    for index, row in df.iterrows():
        try:
            # Get values from CSV columns (Make sure these match your CSV headers exactly!)
            csv_id = row['ID']
            word = row['word']
            synonym = row['synonym word'] # Adjust if your header is different

            # Execute
            val = (csv_id, word, synonym)
            cursor.execute(sql, val)
            inserted_count += 1

        except Exception as e:
            print(f"⚠️ Error inserting row {index}: {e}")
            errors += 1

    # 4. Commit and Close
    conn.commit()
    cursor.close()
    conn.close()
    
    print("-" * 30)
    print(f"🎉 Import Finished!")
    print(f"✅ Successfully inserted: {inserted_count}")
    print(f"❌ Failed rows: {errors}")

if __name__ == "__main__":
    import_csv_to_db()