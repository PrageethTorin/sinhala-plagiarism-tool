# backend/modules/semantic_similarity/approved_hybrid.py

from .custom_algorithms import HybridSimilarityAlgorithm
from .services import FineTunedEmbeddingService


class ApprovedHybridDetector:
    """
    FINAL APPROVED HYBRID DETECTOR
    -----------------------------
    1. Use custom algorithms for easy cases
    2. Use fine-tuned XLM-R for difficult cases (0.4–0.7)
    """

    def __init__(self):
        self.custom_detector = HybridSimilarityAlgorithm()
        self.embedding_service = FineTunedEmbeddingService()

        self.low_threshold = 0.4
        self.high_threshold = 0.7

    def detect(self, text1: str, text2: str):
        # Step 1: Custom similarity
        custom_result = self.custom_detector.calculate_similarity(text1, text2)
        custom_score = custom_result["similarity_score"]

        # Easy negative case
        if custom_score < self.low_threshold:
            return {
                "final_score": custom_score,
                "custom_score": custom_score,
                "embedding_score": None,
                "case_type": "easy_negative",
                "method": "custom_only"
            }

        # Easy positive case
        if custom_score > self.high_threshold:
            return {
                "final_score": custom_score,
                "custom_score": custom_score,
                "embedding_score": None,
                "case_type": "easy_positive",
                "method": "custom_only"
            }

        # Difficult case → use fine-tuned model
        embedding_score = self.embedding_service.similarity(text1, text2)
        final_score = (custom_score + embedding_score) / 2

        return {
            "final_score": final_score,
            "custom_score": custom_score,
            "embedding_score": embedding_score,
            "case_type": "difficult",
            "method": "hybrid_fine_tuned"
        }
