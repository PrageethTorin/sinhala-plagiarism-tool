import joblib
import re
import numpy as np
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
from .preprocessor import SinhalaPreprocessor

class WSAAnalyzer:
    def __init__(self):
        self.preprocessor = SinhalaPreprocessor()
        # පර්යේෂණාත්මක ආකෘති පූරණය කිරීම
        self.vectorizer = joblib.load(Path(__file__).resolve().parent / "vectorizer.pkl")
        self.tfidf_matrix = joblib.load(Path(__file__).resolve().parent / "tfidf_matrix.pkl")

    def get_ttr_score(self, text: str):
        """ශබ්දකෝෂ පොහොසත්කම (TTR) ගණනය කිරීම."""
        words = text.strip().split()
        if not words: return 0
        return (len(set(words)) / len(words)) * 100

    def analyze_hybrid_ratio(self, text: str):
        """නිර්ණායක දෙකම (Length & Richness) පරීක්ෂා කිරීමේ තර්කනය."""
        sentences = [s.strip() for s in re.split(r'[.|।|?|!|.]', text) if s.strip()]
        total_count = len(sentences)
        
        if total_count < 1: return {"style_change_ratio": 0.0, "flagged_count": 0}

        lengths = [len(s.split()) for s in sentences]
        ttr_scores = [self.get_ttr_score(s) for s in sentences]
        
        # පරාමිතීන් ගණනය කිරීම
        mean_len = np.mean(lengths)
        std_len = np.std(lengths)
        mean_ttr = np.mean(ttr_scores)
        
        flagged_count = 0
        sentence_map = []
        
        for i, (length, ttr) in enumerate(zip(lengths, ttr_scores)):
            # 1) වාක්‍ය දිග පරීක්ෂාව: සාමාන්‍ය දිගට වඩා 1.2 ගුණයකට වඩා වැඩි වීම
            is_length_spike = (length > (mean_len + (std_len * 1.2)))
            
            # 2) ශබ්දකෝෂ පොහොසත්කම පරීක්ෂාව: TTR 100% වීම සහ වචන 8 කට වැඩි වීම
            is_richness_spike = (ttr == 100.0 and length > 8 and ttr > mean_ttr)
            
            # නිර්ණායක දෙකෙන් එකක් හෝ සපුරාලන්නේ නම්
            is_shift = is_length_spike or is_richness_spike
            
            if is_shift:
                flagged_count += 1
            
            sentence_map.append({
                "id": i + 1,
                "length": length,
                "lexical_ttr": round(ttr, 2),
                "is_outlier": bool(is_shift),
                "category": "STYLE SHIFT" if is_shift else "Baseline"
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
        
        return {
            "similarity_score": round(float(max_score) * 100, 2),
            "ratio_data": self.analyze_hybrid_ratio(input_text)
        }