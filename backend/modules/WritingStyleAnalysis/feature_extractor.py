import re
import os

class SinhalaStylometryExtractor:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.stopword_path = os.path.join(current_dir, 'stopwords_sinhala.txt')
        self.stop_words = self._load_stopwords()
        self.formal_verbs = ['වේය', 'ගියේය', 'ලදී', 'ඇත', 'වෙති', 'කෙරේ', 'විය', 'පවතී', 'බවයි']
        self.academic_connectors = ['සහ', 'හා', 'මගින්', 'විසින්', 'සඳහා', 'පිළිබඳ', 'එබැවින්', 'තවද']

    def _load_stopwords(self):
        if not os.path.exists(self.stopword_path): return []
        with open(self.stopword_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]

    def analyze_style(self, text):
        tokens = re.sub(r'[^\w\s]', '', text).split()
        clean_tokens = [t for t in tokens if t not in self.stop_words]
        
        # 4 Core Features
        sentence_length = float(len(tokens))
        vocabulary_richness = float(len(set(clean_tokens)) / len(clean_tokens)) if clean_tokens else 0.0
        punc_chars = [c for c in text if c in [',', ';', '?', '!', ':']]
        punctuation_density = float(len(punc_chars) / len(tokens)) if tokens else 0.0
        
        formal_hits = sum(1 for verb in self.formal_verbs if verb in text)
        connector_hits = sum(1 for conn in self.academic_connectors if conn in text)
        linguistic_bias = float(formal_hits + connector_hits)

        return {
            "sentence_length": sentence_length,
            "vocabulary_richness": vocabulary_richness,
            "punctuation_density": punctuation_density,
            "linguistic_bias": linguistic_bias
        }