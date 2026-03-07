# synonym_map.py
"""
Loads and provides Sinhala synonyms from CSV for word replacement suggestions
"""
import os
import csv

# Load synonyms from CSV at startup
_synonyms_dict = {}
_csv_path = os.path.join(os.path.dirname(__file__), '../../data/Dataset(synonyms ).csv')

try:
    if os.path.exists(_csv_path):
        with open(_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                word = row.get('word', '').strip()
                synonym = row.get('synonym word', '').strip()
                
                if word and synonym:
                    if word not in _synonyms_dict:
                        _synonyms_dict[word] = []
                    if synonym not in _synonyms_dict[word]:
                        _synonyms_dict[word].append(synonym)
        print(f"✅ Loaded {len(_synonyms_dict)} words with synonyms from CSV")
except Exception as e:
    print(f"⚠️ Warning: Could not load synonyms CSV: {e}")

# Fallback hardcoded synonyms if CSV fails
FALLBACK_SYNONYMS = {
    "ප්‍රගමනය": ["දියුණුව", "ඉදිරියට යාම"],
    "ප්‍රතිපාදන": ["මුදල්", "සම්පත්"],
    "විශ්ලේෂණය": ["පරීක්ෂා කිරීම", "විමසා බැලීම"],
    "අනන්‍යතාවය": ["සැබෑ තත්ත්වය", "හඳුනාගැනීම"],
    "ක්‍රියාවලිය": ["වැඩපිළිවෙළ", "පියවර මාලාව"],
    "සංකල්පය": ["අදහස", "මූලධර්මය"],
    "ප්‍රතිසංස්කරණය": ["අලුත්වැඩියාව", "සැකසීම"]
}

def get_synonyms(word):
    """
    Get list of synonyms for a given Sinhala word.
    First tries CSV-loaded synonyms, then falls back to hardcoded.
    
    Args:
        word (str): The Sinhala word to find synonyms for
        
    Returns:
        list: List of synonyms, or empty list if none found
    """
    if not word:
        return []
    
    word = word.strip()
    
    # Try CSV-loaded synonyms first
    if word in _synonyms_dict:
        return _synonyms_dict[word][:3]  # Return max 3 suggestions
    
    # Fall back to hardcoded synonyms
    return FALLBACK_SYNONYMS.get(word, [])