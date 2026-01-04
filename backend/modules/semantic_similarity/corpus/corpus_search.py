"""
Corpus Search with FAISS Index
Provides similarity search over the local Sinhala web corpus
"""

import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

# Paths using absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.dirname(BASE_DIR)
DB_PATH = os.path.join(BASE_DIR, "corpus.db")
INDEX_PATH = os.path.join(BASE_DIR, "faiss_index.bin")
TEXTS_PATH = os.path.join(BASE_DIR, "corpus_texts.pkl")
MODEL_PATH = os.path.join(MODULE_DIR, "sinhala_fine_tuned_model")

# Lazy loading for model and index
_model = None
_index = None


def _get_model():
    """Lazy load the sentence transformer model"""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            if os.path.exists(MODEL_PATH):
                _model = SentenceTransformer(MODEL_PATH)
            else:
                # Fallback to multilingual model
                _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
                logger.info("Using fallback multilingual model")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    return _model


def _get_index():
    """Lazy load the FAISS index"""
    global _index
    if _index is None:
        try:
            import faiss
            if os.path.exists(INDEX_PATH):
                _index = faiss.read_index(INDEX_PATH)
            else:
                logger.warning(f"FAISS index not found at {INDEX_PATH}")
                return None
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            return None
    return _index


class CorpusSearcher:
    """Search the local Sinhala corpus using FAISS"""

    def __init__(self):
        self.model = None
        self.index = None
        self._initialized = False

    def _initialize(self):
        """Initialize model and index on first use"""
        if self._initialized:
            return

        try:
            self.model = _get_model()
            self.index = _get_index()
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize CorpusSearcher: {e}")
            self._initialized = True  # Prevent repeated init attempts

    def search(self, query: str, top_k: int = 10):
        """
        Search the corpus for similar texts

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of dicts with matched_text and score
        """
        self._initialize()

        if self.index is None:
            logger.warning("FAISS index not available")
            return []

        if self.model is None:
            logger.warning("Model not available")
            return []

        try:
            import faiss
            import numpy as np

            # Encode query
            query_emb = self.model.encode([query], convert_to_numpy=True)
            faiss.normalize_L2(query_emb)

            # Search index
            scores, indices = self.index.search(query_emb, top_k)

            # Fetch texts from database
            results = []
            if os.path.exists(DB_PATH):
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                for i, idx in enumerate(indices[0]):
                    if idx >= 0:  # Valid index
                        cursor.execute(
                            "SELECT text FROM corpus WHERE id=?",
                            (int(idx + 1),)
                        )
                        row = cursor.fetchone()
                        if row:
                            results.append({
                                "matched_text": row[0],
                                "score": float(scores[0][i])
                            })

                conn.close()

            return results

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []


def get_top_web_candidates(query: str, top_k: int = 10):
    """
    Legacy function for backward compatibility

    Args:
        query: Search query
        top_k: Number of results

    Returns:
        List of matched texts
    """
    searcher = CorpusSearcher()
    results = searcher.search(query, top_k)
    return [r["matched_text"] for r in results]
