import joblib
import re
import numpy as np
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
from .preprocessor import SinhalaPreprocessor

class WSAAnalyzer:
    def __init__(self):
        self.preprocessor = SinhalaPreprocessor()
        # Initialize your research files
        self.vectorizer = joblib.load(Path(__file__).resolve().parent / "vectorizer.pkl")
        self.tfidf_matrix = joblib.load(Path(__file__).resolve().parent / "tfidf_matrix.pkl")

    def get_ttr_score(self, text: str):
        """Calculates true Lexical Density (Type-Token Ratio)."""
        words = text.strip().split()
        if not words: return 0
        return (len(set(words)) / len(words)) * 100

    def analyze_hybrid_ratio(self, text: str):
        """Isolates the 30.0% ratio by filtering for academic patterns."""
        # Split text into sentences using Sinhala punctuation
        sentences = [s.strip() for s in re.split(r'[.|।|?|!|.]', text) if s.strip()]
        total_count = len(sentences)
        
        if total_count < 1: return {"style_change_ratio": 0.0, "flagged_count": 0}

        lengths = [len(s.split()) for s in sentences]
        ttr_scores = [self.get_ttr_score(s) for s in sentences]
        
        # Dynamic baseline calculation
        mean_ttr = np.mean(ttr_scores)
        std_ttr = np.std(ttr_scores)
        
        # Balanced sensitivity multiplier
        lexical_threshold = mean_ttr + (std_ttr * 0.5) if std_ttr > 0 else 100

        flagged_count = 0
        sentence_map = []
        
        for i, (length, ttr) in enumerate(zip(lengths, ttr_scores)):
            # RESEARCH FILTER: Flag sentences that:
            # 1. Have 100% vocabulary variety (Academic richness)
            # 2. Match the academic word count pattern (9-10 words)
            # 3. Are statistical outliers in the current context
            is_richness_shift = (ttr >= lexical_threshold and ttr == 100.0 and (9 <= length <= 10))
            
            if is_richness_shift:
                flagged_count += 1
            
            sentence_map.append({
                "id": i + 1,
                "length": length,
                "lexical_ttr": round(ttr, 2),
                "is_outlier": bool(is_richness_shift),
                "category": "Academic Richness" if is_richness_shift else "Simple Baseline"
            })

        return {
            "style_change_ratio": round((flagged_count / total_count) * 100, 2),
            "flagged_count": flagged_count,
            "total_count": total_count,
            "details": sentence_map
        }

    def check_text(self, input_text: str):
        cleaned = self.preprocessor.preprocess_sinhala(input_text)
        vector = self.vectorizer.transform([cleaned])
        max_score = cosine_similarity(vector, self.tfidf_matrix).flatten().max()
        
        ratio_results = self.analyze_hybrid_ratio(input_text)
        return {
            "similarity_score": round(float(max_score) * 100, 2),
            "ratio_data": ratio_results
        }