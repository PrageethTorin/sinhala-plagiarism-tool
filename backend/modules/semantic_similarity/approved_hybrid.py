# backend/modules/semantic_similarity/approved_hybrid.py

from .custom_algorithms import HybridSimilarityAlgorithm
from .services import FineTunedEmbeddingService


class ApprovedHybridDetector:
    """
    FINAL APPROVED HYBRID DETECTOR (UPDATED V2)
    -------------------------------------------
    ALWAYS uses both custom algorithm AND fine-tuned ML model.
    This catches paraphrases where words are different but meaning is same.

    Case Types:
    - paraphrase_detected: High embedding (>=0.6) + Low custom (<0.5) = PARAPHRASE!
    - easy_positive: Both scores high = Clear match
    - easy_negative: Both scores low = Not related
    - difficult: Mixed signals = Needs analysis
    """

    def __init__(self):
        self.custom_detector = HybridSimilarityAlgorithm()
        self.embedding_service = FineTunedEmbeddingService()

    def detect(self, text1: str, text2: str):
        """
        Detect similarity using BOTH custom algorithm and fine-tuned ML model.
        Always calculates embedding score to catch paraphrases.
        """
        # Step 1: Custom similarity (Jaccard + N-grams + Word Order)
        custom_result = self.custom_detector.calculate_similarity(text1, text2)
        custom_score = custom_result["similarity_score"]

        # Step 2: ALWAYS calculate embedding score (fine-tuned ML model)
        embedding_score = self.embedding_service.similarity(text1, text2)

        # Step 3: Determine case type based on BOTH scores
        if embedding_score >= 0.6:
            if custom_score >= 0.5:
                # Both high = clear match
                case_type = "easy_positive"
                final_score = (custom_score + embedding_score) / 2
                method = "hybrid_fine_tuned"
            else:
                # High embedding + Low custom = PARAPHRASE DETECTED!
                # Same meaning, different words
                case_type = "paraphrase_detected"
                final_score = embedding_score  # Trust the semantic model
                method = "embedding_primary"
        elif embedding_score < 0.3 and custom_score < 0.3:
            # Both low = clearly not related
            case_type = "easy_negative"
            final_score = (custom_score + embedding_score) / 2
            method = "hybrid_fine_tuned"
        else:
            # Mixed signals = difficult case
            case_type = "difficult"
            final_score = (custom_score + embedding_score) / 2
            method = "hybrid_fine_tuned"

        return {
            "final_score": final_score,
            "custom_score": custom_score,
            "embedding_score": embedding_score,
            "case_type": case_type,
            "method": method,
            "code_version": "V2_ALWAYS_ML"
        }
