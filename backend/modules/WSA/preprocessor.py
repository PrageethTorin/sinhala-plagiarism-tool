import re

class SinhalaPreprocessor:
    def __init__(self):
        # You can add a list of Sinhala stopwords here later if needed
        pass

    def preprocess_sinhala(self, text: str):
        if not text:
            return ""
        # 1. Remove punctuation and special characters, keeping only Sinhala Unicode range
        text = re.sub(r'[^\u0D80-\u0DFF\s]', '', text)
        # 2. Remove extra whitespaces and newlines
        text = " ".join(text.split())
        return text