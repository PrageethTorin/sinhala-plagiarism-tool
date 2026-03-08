# modules/ParaphraseDetection/lexical_analyzer.py
import sys
import os
import mysql.connector

# Add the backend folder to the system path to find 'database/db_config.py'
# We go up two levels: ParaphraseDetection -> modules -> backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from database.db_config import get_db_connection

def get_synonyms_from_db(word):
    """
    Fetches all synonyms for a given word from the MySQL database.
    Checks both 'word' and 'synonym_word' columns.
    """
    synonyms = set()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check both directions: Word -> Synonym AND Synonym -> Word
        query = """
            SELECT synonym_word FROM synonyms WHERE word = %s
            UNION
            SELECT word FROM synonyms WHERE synonym_word = %s
        """
        cursor.execute(query, (word, word))
        results = cursor.fetchall()
        
        for row in results:
            if row[0]:
                # CRITICAL FIX: .strip() removes invisible spaces/newlines
                clean_word = row[0].strip()
                synonyms.add(clean_word)
                
    except mysql.connector.Error as err:
        print(f"⚠️ DB Error: {err}")
    finally:
        if conn and conn.is_connected():
            conn.close()
            
    return synonyms

def calculate_lexical_similarity(tokens1, tokens2):
    """
    Calculates overlap between two lists of tokens.
    Returns a score between 0.0 and 1.0.
    """
    if not tokens1 or not tokens2:
        return 0.0
        
    match_count = 0
    # Create a copy of tokens2 so we don't accidentally modify the original list
    temp_tokens2 = list(tokens2)
    
    for word1 in tokens1:
        # 1. Direct Match (Exact word)
        if word1 in temp_tokens2:
            match_count += 1
            temp_tokens2.remove(word1) # Remove so we don't count it twice
            continue
            
        # 2. Synonym Match (Check Database)
        synonyms = get_synonyms_from_db(word1)
        found_synonym = False
        
        for syn in synonyms:
            if syn in temp_tokens2:
                match_count += 1
                temp_tokens2.remove(syn)
                found_synonym = True
                # Success message to confirm it worked
                print(f"   ✅ Synonym Matched: '{word1}' == '{syn}'")
                break
        
        if not found_synonym:
            pass # No match found
            
    # Calculate Score: Matches / Length of the longer sentence
    max_len = max(len(tokens1), len(tokens2))
    return match_count / max_len if max_len > 0 else 0