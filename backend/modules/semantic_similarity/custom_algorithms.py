"""
Custom plagiarism detection algorithms for Sinhala text
No pre-trained models used - pure statistical methods
"""
import re
import math
from collections import Counter
from typing import List, Dict, Tuple, Any


class SinhalaTextProcessor:
    """Process Sinhala text for similarity analysis"""
    
    SINHALA_STOPWORDS = {
        'මම', 'ඔබ', 'එය', 'සහ', 'නමුත්', 'හෝ', 'ඒ', 'මෙය', 'අප', 'ඔවුන්',
        'කොහේ', 'කවුද', 'මොකද', 'කොහොමද', 'කවදා', 'කොහෙන්', 'මට', 'ඔහු',
        'ඇය', 'එහි', 'මෙහි', 'එම', 'මෙම', 'එවිට', 'මෙවිට', 'එසේ', 'මෙසේ'
    }
    
    @staticmethod
    def preprocess(text: str) -> List[str]:
        """Clean and tokenize Sinhala text"""
        # Remove punctuation and numbers
        text = re.sub(r'[^\w\s\u0D80-\u0DFF]', ' ', text)
        # Tokenize
        tokens = text.split()
        # Remove stopwords and short tokens
        tokens = [t for t in tokens if t not in SinhalaTextProcessor.SINHALA_STOPWORDS and len(t) > 1]
        return tokens
    
    @staticmethod
    def get_ngrams(text: str, n: int = 3) -> List[str]:
        """Get character n-grams from text"""
        # Remove spaces for character n-grams
        text = re.sub(r'\s+', '', text)
        if len(text) < n:
            return [text]
        return [text[i:i+n] for i in range(len(text) - n + 1)]


class HybridSimilarityAlgorithm:
    """
    Main hybrid algorithm combining Jaccard, N-gram, and Word Order similarities
    """
    
    def __init__(self, weights: Dict[str, float] = None):
        """Initialize with custom weights"""
        self.processor = SinhalaTextProcessor()
        self.weights = weights or {
            'jaccard': 0.4,
            'ngram_2': 0.2,
            'ngram_3': 0.2,
            'word_order': 0.2
        }
        # Validate weights sum to 1
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError("Weights must sum to 1.0")
    
    def jaccard_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between word sets"""
        set1 = set(self.processor.preprocess(text1))
        set2 = set(self.processor.preprocess(text2))
        
        if not set1 and not set2:
            return 1.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def ngram_similarity(self, text1: str, text2: str, n: int = 3) -> float:
        """Calculate n-gram similarity"""
        ngrams1 = set(self.processor.get_ngrams(text1, n))
        ngrams2 = set(self.processor.get_ngrams(text2, n))
        
        if not ngrams1 and not ngrams2:
            return 1.0
        
        intersection = len(ngrams1.intersection(ngrams2))
        union = len(ngrams1.union(ngrams2))
        
        return intersection / union if union > 0 else 0.0
    
    def word_order_similarity(self, text1: str, text2: str) -> float:
        """Calculate word order similarity"""
        tokens1 = self.processor.preprocess(text1)
        tokens2 = self.processor.preprocess(text2)
        
        # Find common words
        common = set(tokens1).intersection(set(tokens2))
        if not common or len(common) < 2:
            return 0.5  # Neutral score for few common words
        
        # Get positions of common words
        pos1 = {word: i for i, word in enumerate(tokens1) if word in common}
        pos2 = {word: i for i, word in enumerate(tokens2) if word in common}
        
        # Ensure same words in both
        common_words = list(common)
        
        # Calculate position differences
        diffs = []
        for word in common_words:
            if word in pos1 and word in pos2:
                diffs.append(abs(pos1[word] - pos2[word]))
        
        if not diffs:
            return 0.5
        
        # Normalize: 1 - (avg_diff / max_possible_diff)
        avg_diff = sum(diffs) / len(diffs)
        max_possible = max(len(tokens1), len(tokens2))
        normalized_diff = avg_diff / max_possible if max_possible > 0 else 1
        
        return 1 - normalized_diff
    
    def calculate_similarity(self, text1: str, text2: str) -> Dict[str, Any]:
        """
        Calculate hybrid similarity score
        Returns: {
            'similarity_score': float,
            'components': Dict[str, float],
            'algorithm': str
        }
        """
        # Calculate individual components
        components = {
            'jaccard': self.jaccard_similarity(text1, text2),
            'ngram_2': self.ngram_similarity(text1, text2, n=2),
            'ngram_3': self.ngram_similarity(text1, text2, n=3),
            'word_order': self.word_order_similarity(text1, text2)
        }
        
        # Calculate weighted score
        weighted_score = sum(
            components[name] * weight 
            for name, weight in self.weights.items()
        )
        
        # Clamp to [0, 1]
        weighted_score = max(0.0, min(1.0, weighted_score))
        
        return {
            'similarity_score': weighted_score,
            'components': components,
            'algorithm': 'custom_hybrid_v1',
            'weights_used': self.weights
        }