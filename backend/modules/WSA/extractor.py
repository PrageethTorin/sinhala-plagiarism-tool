# extractor.py
import re

# Standard Sinhala particles used for stylometric "Fingerprinting"
# These are kept and measured as 'Function Words' rather than being removed like stopwords.
SINHALA_FUNCTION_WORDS = [
    "සහ", "හා", "ද", "ම", "මෙන්ම", "නමුත්", "සඳහා", "මගින්", 
    "විසින්", "ගැන", "පිළිබඳව", "වෙත", "තෙක්", "දක්වා", "එමෙන්ම", 
    "නැතහොත්", "හෙවත්", "කෙරෙහි", "සමඟ", "සමග", "වඩා", "වැනි", "විට"
]

class StyleExtractor:
    def __init__(self):
        pass

    def calculate_avg_sentence_length(self, sentences):
        """Calculates the average number of words per sentence."""
        if not sentences:
            return 0
        
        total_words = sum(len(s.split()) for s in sentences)
        return round(total_words / len(sentences), 2)

    def calculate_vocabulary_richness(self, sentences):
        """
        Calculates Type-Token Ratio (TTR).
        Higher values indicate a more diverse and formal vocabulary.
        """
        all_words = []
        for s in sentences:
            all_words.extend(s.split())
        
        if not all_words:
            return 0
        
        unique_words = set(all_words)
        # TTR = (Number of unique words / Total number of words)
        return round(len(unique_words) / len(all_words), 4)

    def calculate_punctuation_density(self, raw_text, total_words):
        """Calculates the frequency of punctuation marks per word."""
        if total_words == 0:
            return 0
        
        # Count Sinhala/Common punctuation: . , ? ! |
        punctuation_marks = [char for char in raw_text if char in ".,?!|"]
        return round(len(punctuation_marks) / total_words, 4)

    def calculate_function_word_frequency(self, words):
        """
        Standard Level Research Feature:
        Calculates the ratio of Sinhala particles (function words) to total words.
        Authors use these particles at very consistent rates.
        """
        if not words:
            return 0
        
        # Count occurrences of words in the function word list
        count = sum(1 for word in words if word in SINHALA_FUNCTION_WORDS)
        return round(count / len(words), 4)

    def get_all_features(self, raw_text, sentences):
        """
        Compiles all stylometric features into a single dictionary.
        This provides a 4-dimensional vector for the ML model.
        """
        all_words = []
        for s in sentences:
            all_words.extend(s.split())
            
        total_words = len(all_words)
        
        features = {
            'avg_sentence_length': self.calculate_avg_sentence_length(sentences),
            'vocabulary_richness': self.calculate_vocabulary_richness(sentences),
            'punctuation_density': self.calculate_punctuation_density(raw_text, total_words),
            'function_word_freq': self.calculate_function_word_frequency(all_words)
        }
        return features