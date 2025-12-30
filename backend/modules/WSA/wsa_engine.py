import joblib
import re
import numpy as np
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
from .preprocessor import SinhalaPreprocessor

# Path Setup
CURRENT_DIR = Path(__file__).resolve().parent
VECTORIZER_PATH = CURRENT_DIR / "vectorizer.pkl"
MATRIX_PATH = CURRENT_DIR / "tfidf_matrix.pkl"
DATA_PATH = CURRENT_DIR / "wsa_model.pkl"

class WSAAnalyzer:
    def __init__(self):
        self.preprocessor = SinhalaPreprocessor()
        try:
            self.vectorizer = joblib.load(VECTORIZER_PATH)
            self.tfidf_matrix = joblib.load(MATRIX_PATH)
            self.df_train = joblib.load(DATA_PATH)
            print("✅ WSA Engine: Dynamic Ratio Analysis Active.")
        except Exception as e:
            print(f"❌ Initialization Error: {e}")

    def calculate_dynamic_ratio(self, text: str):
        """Logic: Identifies outliers based on mean and standard deviation."""
        # Split into sentences
        sentences = [s.strip() for s in re.split(r'[.|।|?|!|.]', text) if s.strip()]
        total_count = len(sentences)
        
        if total_count < 2:
            return {"ratio": 0.0, "flagged": 0, "total": total_count, "map": []}

        # Calculate word counts
        lengths = [len(s.split()) for s in sentences]
        
        # DYNAMIC CALCULATION: Using Mean and Standard Deviation
        mean_len = np.mean(lengths)
        std_dev = np.std(lengths)
        
        # Threshold: If a sentence length is more than 1.5 StdDev away from mean, it's a style shift
        threshold = std_dev * 1.5
        
        flagged_count = 0
        sentence_map = []
        
        for i, length in enumerate(lengths):
            # Check if this sentence is an outlier
            is_outlier = abs(length - mean_len) > threshold
            
            if is_outlier:
                flagged_count += 1
            
            sentence_map.append({
                "id": i + 1,
                "length": length,
                "is_outlier": bool(is_outlier)
            })

        # Final dynamic percentage calculation
        ratio_percentage = (flagged_count / total_count) * 100

        return {
            "style_change_ratio": round(ratio_percentage, 2),
            "flagged_count": flagged_count,
            "total_count": total_count,
            "details": sentence_map
        }

    def check_text(self, input_text: str):
        cleaned = self.preprocessor.preprocess_sinhala(input_text)
        vector = self.vectorizer.transform([cleaned])
        similarities = cosine_similarity(vector, self.tfidf_matrix).flatten()
        max_score = similarities.max()
        
        # Dynamic ratio analysis
        ratio_results = self.calculate_dynamic_ratio(input_text)
        
        return {
            "similarity_score": round(float(max_score) * 100, 2),
            "ratio_data": ratio_results
        }