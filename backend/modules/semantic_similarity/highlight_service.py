"""
Semantic Word Highlighting Service
===================================
Highlights semantically similar words between original and suspicious text.
Uses the fine-tuned MiniLM model to find word-level semantic matches.

Author: S N S Dahanayake (IT22920522)
Created: January 10, 2026
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np

# Import from existing services
from .services import FineTunedEmbeddingService, SinhalaTextProcessor


@dataclass
class WordPosition:
    """Represents a word with its position in text."""
    word: str
    start: int
    end: int
    index: int


@dataclass
class HighlightMatch:
    """Represents a semantic match between words."""
    suspicious_word: str
    original_word: str
    start: int
    end: int
    similarity: float
    highlight_color: str


class SemanticHighlightService:
    """
    Service for highlighting semantically similar words between texts.

    This service:
    1. Tokenizes both original and suspicious texts with position tracking
    2. Gets embeddings for each meaningful word
    3. Finds best semantic matches between suspicious and original words
    4. Returns highlights with positions, scores, and color codes
    """

    # Color thresholds for highlighting
    HIGH_SIMILARITY_THRESHOLD = 0.8    # Red - very high similarity
    MEDIUM_SIMILARITY_THRESHOLD = 0.6  # Orange - medium similarity
    LOW_SIMILARITY_THRESHOLD = 0.4     # Yellow - low but notable similarity

    # Color codes
    COLOR_HIGH = "#ff6b6b"      # Red
    COLOR_MEDIUM = "#ffa94d"    # Orange
    COLOR_LOW = "#ffd43b"       # Yellow

    def __init__(self):
        """Initialize the highlighting service with embedding model."""
        self.embedding_service = FineTunedEmbeddingService()
        self.text_processor = SinhalaTextProcessor()

    def _tokenize_with_positions(self, text: str) -> List[WordPosition]:
        """
        Tokenize text while keeping track of character positions.

        Args:
            text: Input text to tokenize

        Returns:
            List of WordPosition objects with word, start, end positions
        """
        positions = []

        # Use regex to find all words with their positions
        # This pattern matches Sinhala Unicode characters and English alphanumeric
        pattern = r'[\u0D80-\u0DFF]+|[a-zA-Z0-9]+'

        for idx, match in enumerate(re.finditer(pattern, text)):
            word = match.group()
            # Skip stopwords and very short words
            if word not in self.text_processor.sinhala_stopwords and len(word) > 1:
                positions.append(WordPosition(
                    word=word,
                    start=match.start(),
                    end=match.end(),
                    index=idx
                ))

        return positions

    def _get_word_embeddings(self, words: List[str]) -> np.ndarray:
        """
        Get embeddings for a list of words.

        Args:
            words: List of words to embed

        Returns:
            Numpy array of embeddings (n_words x embedding_dim)
        """
        if not words:
            return np.array([])

        # Use the fine-tuned model to get embeddings
        embeddings = self.embedding_service.model.encode(
            words,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        return embeddings

    def _calculate_similarity_matrix(
        self,
        suspicious_embeddings: np.ndarray,
        original_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Calculate cosine similarity matrix between suspicious and original word embeddings.

        Args:
            suspicious_embeddings: Embeddings of suspicious text words
            original_embeddings: Embeddings of original text words

        Returns:
            Similarity matrix (n_suspicious x n_original)
        """
        if len(suspicious_embeddings) == 0 or len(original_embeddings) == 0:
            return np.array([])

        # Cosine similarity (embeddings are already normalized)
        similarity_matrix = np.dot(suspicious_embeddings, original_embeddings.T)

        return similarity_matrix

    def _get_highlight_color(self, similarity: float) -> str:
        """
        Get highlight color based on similarity score.

        Args:
            similarity: Similarity score (0-1)

        Returns:
            Hex color code
        """
        if similarity >= self.HIGH_SIMILARITY_THRESHOLD:
            return self.COLOR_HIGH
        elif similarity >= self.MEDIUM_SIMILARITY_THRESHOLD:
            return self.COLOR_MEDIUM
        elif similarity >= self.LOW_SIMILARITY_THRESHOLD:
            return self.COLOR_LOW
        else:
            return ""  # No highlight

    def get_highlighted_matches(
        self,
        original: str,
        suspicious: str,
        threshold: float = 0.4
    ) -> Dict:
        """
        Find and highlight semantically similar words between texts.

        Args:
            original: Original/source text
            suspicious: Text to check for similarity
            threshold: Minimum similarity score to highlight (default 0.4)

        Returns:
            Dictionary with:
            - highlights: List of HighlightMatch objects
            - suspicious_text: Original suspicious text
            - original_text: Original text
            - statistics: Match statistics
        """
        # Step 1: Tokenize both texts with positions
        suspicious_positions = self._tokenize_with_positions(suspicious)
        original_positions = self._tokenize_with_positions(original)

        if not suspicious_positions or not original_positions:
            return {
                "highlights": [],
                "suspicious_text": suspicious,
                "original_text": original,
                "statistics": {
                    "total_suspicious_words": len(suspicious_positions),
                    "total_original_words": len(original_positions),
                    "matched_words": 0,
                    "average_similarity": 0.0
                }
            }

        # Step 2: Get embeddings for all words
        suspicious_words = [wp.word for wp in suspicious_positions]
        original_words = [wp.word for wp in original_positions]

        suspicious_embeddings = self._get_word_embeddings(suspicious_words)
        original_embeddings = self._get_word_embeddings(original_words)

        # Step 3: Calculate similarity matrix
        similarity_matrix = self._calculate_similarity_matrix(
            suspicious_embeddings,
            original_embeddings
        )

        if similarity_matrix.size == 0:
            return {
                "highlights": [],
                "suspicious_text": suspicious,
                "original_text": original,
                "statistics": {
                    "total_suspicious_words": len(suspicious_positions),
                    "total_original_words": len(original_positions),
                    "matched_words": 0,
                    "average_similarity": 0.0
                }
            }

        # Step 4: Find best matches for each suspicious word
        highlights = []
        similarities = []

        for i, susp_pos in enumerate(suspicious_positions):
            # Find the best matching original word
            best_match_idx = np.argmax(similarity_matrix[i])
            best_similarity = similarity_matrix[i][best_match_idx]

            # Only include if above threshold
            if best_similarity >= threshold:
                orig_pos = original_positions[best_match_idx]
                color = self._get_highlight_color(best_similarity)

                if color:  # Only add if we have a color (above minimum threshold)
                    highlight = HighlightMatch(
                        suspicious_word=susp_pos.word,
                        original_word=orig_pos.word,
                        start=susp_pos.start,
                        end=susp_pos.end,
                        similarity=float(best_similarity),
                        highlight_color=color
                    )
                    highlights.append(highlight)
                    similarities.append(best_similarity)

        # Calculate statistics
        avg_similarity = float(np.mean(similarities)) if similarities else 0.0

        return {
            "highlights": [
                {
                    "suspicious_word": h.suspicious_word,
                    "original_word": h.original_word,
                    "start": h.start,
                    "end": h.end,
                    "similarity": round(h.similarity, 4),
                    "highlight_color": h.highlight_color
                }
                for h in highlights
            ],
            "suspicious_text": suspicious,
            "original_text": original,
            "statistics": {
                "total_suspicious_words": len(suspicious_positions),
                "total_original_words": len(original_positions),
                "matched_words": len(highlights),
                "average_similarity": round(avg_similarity, 4),
                "high_similarity_count": sum(1 for h in highlights if h.highlight_color == self.COLOR_HIGH),
                "medium_similarity_count": sum(1 for h in highlights if h.highlight_color == self.COLOR_MEDIUM),
                "low_similarity_count": sum(1 for h in highlights if h.highlight_color == self.COLOR_LOW)
            }
        }

    def get_highlighted_html(
        self,
        original: str,
        suspicious: str,
        threshold: float = 0.4
    ) -> str:
        """
        Generate HTML with highlighted words.

        Args:
            original: Original text
            suspicious: Suspicious text
            threshold: Minimum similarity threshold

        Returns:
            HTML string with highlighted suspicious text
        """
        result = self.get_highlighted_matches(original, suspicious, threshold)

        if not result["highlights"]:
            return suspicious

        # Sort highlights by start position (reverse order for replacement)
        highlights = sorted(result["highlights"], key=lambda x: x["start"], reverse=True)

        html_text = suspicious

        for h in highlights:
            before = html_text[:h["start"]]
            word = html_text[h["start"]:h["end"]]
            after = html_text[h["end"]:]

            # Create highlighted span with tooltip
            highlighted = (
                f'<span class="semantic-highlight" '
                f'style="background-color: {h["highlight_color"]}; padding: 2px 4px; border-radius: 3px;" '
                f'title="Matched: {h["original_word"]} ({h["similarity"]*100:.1f}%)">'
                f'{word}</span>'
            )

            html_text = before + highlighted + after

        return html_text


# Singleton instance for reuse
_highlight_service_instance = None

def get_highlight_service() -> SemanticHighlightService:
    """Get or create the singleton highlight service instance."""
    global _highlight_service_instance
    if _highlight_service_instance is None:
        _highlight_service_instance = SemanticHighlightService()
    return _highlight_service_instance
