# backend/modules/ParaphraseDetection/preprocessor.py
import os
import re
import unicodedata
from sinling import SinhalaTokenizer, SinhalaStemmer # <--- NEW: Import Stemmer

def normalize_sinhala(text):
    """
    Standardizes Sinhala text.
    """
    if not text:
        return ""
    text = unicodedata.normalize('NFC', text)
    text = text.replace('\u200d', '')
    return text

def load_stop_words():
    """
    Loads stop words from file.
    """
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, '..', '..', 'data', 'stopwords.txt')
    
    stop_words = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
            for line in lines:
                if ',' in line:
                    parts = line.split(',')
                    if len(parts) >= 2:
                        stop_words.add(normalize_sinhala(parts[1].strip()))
                else:
                    stop_words.add(normalize_sinhala(line.strip()))
    except FileNotFoundError:
        print(f"⚠️ Warning: Stop words file not found at {file_path}")
    
    return stop_words

# --- THE INDUSTRIAL UPGRADE ---
def preprocess_text(text, return_stems=True):
    """
    Tokenizes, Removes Stop Words, AND Stems the words.
    """
    if not text:
        return []

    # 1. Normalize
    text = normalize_sinhala(text)

    # 2. Remove Punctuation
    clean_text = re.sub(r'[^\u0D80-\u0DFF\s]', '', text)
    
    # 3. Tokenize (Split into words)
    tokenizer = SinhalaTokenizer()
    tokens = tokenizer.tokenize(clean_text)
    
    # 4. Filter Stop Words
    stop_words = load_stop_words()
    filtered_tokens = [word for word in tokens if word not in stop_words]
    
    # 5. STEMMING (The New Logic) 🌿
    # This converts "ගුරුවරුන්ට" (to teachers) -> "ගුරුවරු" (teachers)
    if return_stems:
        stemmer = SinhalaStemmer()
        stemmed_tokens = []
        for word in filtered_tokens:
            try:
                # Get the root word (stem)
                stem = stemmer.stem(word)[0] 
                stemmed_tokens.append(stem)
            except:
                # If stemming fails, keep original word
                stemmed_tokens.append(word)
        return stemmed_tokens
    
    return filtered_tokens