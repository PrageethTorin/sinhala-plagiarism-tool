# extractor.py
import re
import numpy as np

# Standard Sinhala particles for authorial fingerprinting
SINHALA_FUNCTION_WORDS = [
    "සහ", "හා", "ද", "ම", "මෙන්ම", "නමුත්", "සඳහා", "මගින්", 
    "විසින්", "ගැන", "පිළිබඳව", "වෙත", "තෙක්", "දක්වා", "එමෙන්ම", 
    "නැතහොත්", "හෙවත්", "කෙරෙහි", "සමඟ", "සමග", "වඩා", "වැනි", "විට"
]

class StyleExtractor:
    def __init__(self):
        # 1. High-Priority Academic Markers (Tatsama Words)
        self.formal_indicators = [
            "ව්‍යවස්ථාපිතව", "ප්‍රතිපාදන", "අනුකූලව", "විශ්ලේෂණය", "සංකල්පය", 
            "න්‍යායාත්මක", "සම්ප්‍රයුක්ත", "නිර්ණායක", "එසමයෙහි", "භූත විය", 
            "ප්‍රගමනය", "අභිමතාර්ථ", "ක්‍රියාවලිය", "අනන්‍යතාවය", "ප්‍රතිසංස්කරණය"
        ]
        
        # 2. Formal Prefixes common in Sinhala Research Papers
        self.formal_prefixes = ["ප්‍රති", "අන්තර්", "සං", "අභි", "ප්‍ර", "අනු", "වි"]
        
        # 3. Formal Suffixes common in academic text
        self.formal_suffixes = ["කරණය", "තාවය", "ත්වය", "ගත", "ප්‍රයුක්ත"]

    def is_word_a_style_shift(self, word, baseline_avg_len=5):
        """
        Research-Grade Detection: Checks for morphological complexity.
        """
        # A. Check for Conjunct characters (ZWJ clusters like ක්‍ර, ප්‍ර)
        has_complex_cluster = bool("\u200D" in word)
        
        # B. Check for formal academic prefixes/suffixes
        has_formal_prefix = any(word.startswith(p) for p in self.formal_prefixes)
        has_formal_suffix = any(word.endswith(s) for s in self.formal_suffixes)
        
        # C. Check for direct academic matches
        is_academic_keyword = any(marker in word for marker in self.formal_indicators)
        
        # D. Statistical Length Check (1.5x longer than baseline)
        is_long = len(word) > (baseline_avg_len * 1.5)

        return bool(has_complex_cluster or has_formal_prefix or has_formal_suffix or is_academic_keyword or is_long)

    def get_all_features(self, raw_text, sentences):
        """Compiles 4D profile for the ML model."""
        all_words = []
        for s in sentences: all_words.extend(s.split())
        total_words = len(all_words)
        
        avg_word_len = float(np.mean([len(w) for w in all_words])) if all_words else 5.0
        
        return {
            'avg_sentence_length': self.calculate_avg_sentence_length(sentences),
            'vocabulary_richness': self.calculate_vocabulary_richness(sentences),
            'punctuation_density': self.calculate_punctuation_density(raw_text, total_words),
            'function_word_freq': self.calculate_function_word_frequency(all_words),
            'avg_word_length': avg_word_len
        }

    def calculate_avg_sentence_length(self, sentences):
        if not sentences: return 0.0
        total_words = sum(len(s.split()) for s in sentences)
        return float(round(total_words / len(sentences), 2))

    def calculate_vocabulary_richness(self, sentences):
        all_words = []
        for s in sentences: all_words.extend(s.split())
        if not all_words: return 0.0
        unique_words = set(all_words)
        return float(round(len(unique_words) / len(all_words), 4))

    def calculate_punctuation_density(self, raw_text, total_words):
        if total_words == 0: return 0.0
        punctuation_marks = [char for char in raw_text if char in ".,?!|"]
        return float(round(len(punctuation_marks) / total_words, 4))

    def calculate_function_word_frequency(self, words):
        if not words: return 0.0
        count = sum(1 for word in words if word in SINHALA_FUNCTION_WORDS)
        return float(round(count / len(words), 4))