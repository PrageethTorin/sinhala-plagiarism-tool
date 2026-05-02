"""
Web Corpus Similarity Service
Compares user text against FAISS-indexed Sinhala web corpus
"""

import logging

logger = logging.getLogger(__name__)

# Lazy imports to avoid circular dependencies
_corpus_searcher = None
_hybrid_detector = None


def _get_searcher():
    """Lazy load CorpusSearcher"""
    global _corpus_searcher
    if _corpus_searcher is None:
        from .corpus_search import CorpusSearcher
        _corpus_searcher = CorpusSearcher()
    return _corpus_searcher


def _get_detector():
    """Lazy load ApprovedHybridDetector"""
    global _hybrid_detector
    if _hybrid_detector is None:
        from ..approved_hybrid import ApprovedHybridDetector
        _hybrid_detector = ApprovedHybridDetector()
    return _hybrid_detector


class WebCorpusSimilarityService:
    """
    Service for checking similarity against local FAISS-indexed corpus
    """

    def __init__(self):
        logger.info("Initializing WebCorpusSimilarityService...")
        self.searcher = None
        self.detector = None
        self._initialized = False

    def _initialize(self):
        """Lazy initialization"""
        if self._initialized:
            return

        try:
            self.searcher = _get_searcher()
            self.detector = _get_detector()
            self._initialized = True
            logger.info("WebCorpusSimilarityService ready")
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            self._initialized = True

    def check(self, user_text: str):
        """
        Check user text against the corpus

        Args:
            user_text: Text to check for plagiarism

        Returns:
            List of matches with scores
        """
        self._initialize()

        logger.info("Web corpus check started")

        if self.searcher is None:
            logger.warning("Corpus searcher not available")
            return []

        results = self.searcher.search(user_text, top_k=5)
        logger.info(f"FAISS returned {len(results)} candidates")

        final_matches = []

        for r in results:
            try:
                matched_text = r.get("matched_text", "")
                if not matched_text:
                    continue

                logger.debug("Comparing candidate text")

                if self.detector:
                    result = self.detector.detect(user_text, matched_text)
                    final_matches.append({
                        "matched_text": matched_text[:300],
                        "final_score": result["final_score"],
                        "case_type": result["case_type"],
                        "custom_score": result.get("custom_score"),
                        "embedding_score": result.get("embedding_score")
                    })
                else:
                    # Fallback without detector
                    final_matches.append({
                        "matched_text": matched_text[:300],
                        "final_score": r.get("score", 0),
                        "case_type": "faiss_only"
                    })
            except Exception as e:
                logger.error(f"Error comparing text: {e}")
                continue

        logger.info("Web corpus check completed")
        return final_matches
