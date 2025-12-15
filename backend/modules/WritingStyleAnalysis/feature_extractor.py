import re
import json
import os

class SinhalaStylometryExtractor:
    def __init__(self):
        # Automatically find the stop words file in the same folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        stopword_path = os.path.join(current_dir, 'stopwords_sinhala.txt')
        self.stopwords = self._load_stopwords(stopword_path)

    def _load_stopwords(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return set([line.strip() for line in f])
        except FileNotFoundError:
            print("Warning: stopwords_sinhala.txt not found. Function word analysis will be skipped.")
            return set()

    def analyze_style(self, text):
        if not text:
            return None

        # 1. Tokenization (Split into sentences and words)
        # Regex splits by Sinhala (.) or English (.)
        sentences = [s.strip() for s in re.split(r'[.]', text) if s.strip()]
        words = text.split()

        if len(words) == 0:
            return None

        # 2. Average Sentence Length
        avg_sentence_len = len(words) / len(sentences) if sentences else 0

        # 3. Vocabulary Richness (Type-Token Ratio)
        unique_words = set(words)
        vocab_richness = len(unique_words) / len(words)

        # 4. Function Word Frequency
        func_word_counts = {word: 0 for word in self.stopwords}
        for word in words:
            if word in self.stopwords:
                func_word_counts[word] += 1
        
        # 5. Punctuation Density
        punctuation_count = text.count('.') + text.count(',') + text.count(';')
        punctuation_density = punctuation_count / len(words)

        return {
            "avg_sentence_length": round(avg_sentence_len, 2),
            "vocabulary_richness": round(vocab_richness, 4),
            "function_word_freq": json.dumps(func_word_counts, ensure_ascii=False),
            "punctuation_density": round(punctuation_density, 4)
        }