import re

class StyleAnalyzer:
    def __init__(self):
        # List of common Sinhala punctuation marks
        self.punctuation_pattern = r'[၊,;:.!?()\"\'\-\[\]]'

    def analyze_style(self, text: str):
        # 1. Feature: Sentence Length Variation
        # Splits text by Sinhala and standard full stops/question marks
        sentences = [s.strip() for s in re.split(r'[.|।|?|!]', text) if s.strip()]
        words = text.split()
        
        if not sentences or not words:
            return {"error": "Insufficient text for style analysis"}

        avg_sentence_length = len(words) / len(sentences)

        # 2. Feature: Vocabulary Richness (Type-Token Ratio)
        # Higher ratio indicates more advanced/professional writing
        unique_words = len(set(words))
        vocabulary_richness = (unique_words / len(words)) * 100

        # 3. Feature: Punctuation Patterns
        punc_count = len(re.findall(self.punctuation_pattern, text))
        punc_density = (punc_count / len(words)) if len(words) > 0 else 0

        return {
            "avg_sentence_length": round(avg_sentence_length, 2),
            "vocabulary_richness": f"{round(vocabulary_richness, 2)}%",
            "punctuation_density": round(punc_density, 4),
            "word_count": len(words),
            "sentence_count": len(sentences)
        }