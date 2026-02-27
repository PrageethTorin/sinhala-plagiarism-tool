"""
Pydantic models for API request/response
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class TextPair(BaseModel):
    """Text pair for comparison"""
    original: str = Field(..., description="Original text")
    suspicious: str = Field(..., description="Text to check for plagiarism")

class SimilarityRequest(BaseModel):
    """Request model for similarity check"""
    text_pair: TextPair
    threshold: float = Field(0.7, ge=0.0, le=1.0, description="Similarity threshold")
    algorithm: str = Field("semantic", description="Algorithm to use")
    check_paraphrase: bool = Field(False, description="Check for paraphrasing")

class MatchResult(BaseModel):
    """Individual match result"""
    original_segment: str
    suspicious_segment: str
    similarity_score: float
    match_type: str  # "exact", "paraphrase", "semantic"

class ComponentScores(BaseModel):
    """Component similarity scores"""
    semantic: float = 0.0
    lexical: float = 0.0
    structural: float = 0.0
    ngram: float = 0.0

class SimilarityResult(BaseModel):
    """Main result model"""
    similarity_score: float
    is_plagiarized: bool
    confidence: float
    verdict: str  # "Original", "Suspected Plagiarism", "Plagiarized"
    components: ComponentScores
    matches: List[MatchResult] = []
    metadata: Dict[str, Any] = {}
    processing_time: float


# ============================================
# Semantic Word Highlighting Schemas (NEW)
# ============================================

class HighlightRequest(BaseModel):
    """Request model for semantic word highlighting"""
    original: str = Field(..., description="Original text to compare against")
    suspicious: str = Field(..., description="Suspicious text to highlight")
    threshold: float = Field(0.4, ge=0.0, le=1.0, description="Minimum similarity for highlighting")

class HighlightMatch(BaseModel):
    """Individual word highlight match"""
    suspicious_word: str = Field(..., description="Word from suspicious text")
    original_word: str = Field(..., description="Matched word from original text")
    start: int = Field(..., description="Start position in suspicious text")
    end: int = Field(..., description="End position in suspicious text")
    similarity: float = Field(..., description="Semantic similarity score (0-1)")
    highlight_color: str = Field(..., description="Hex color code for highlighting")

class HighlightStatistics(BaseModel):
    """Statistics for the highlighting operation"""
    total_suspicious_words: int = Field(0, description="Total words in suspicious text")
    total_original_words: int = Field(0, description="Total words in original text")
    matched_words: int = Field(0, description="Number of highlighted words")
    average_similarity: float = Field(0.0, description="Average similarity of matches")
    high_similarity_count: int = Field(0, description="Words with >= 80% similarity (red)")
    medium_similarity_count: int = Field(0, description="Words with 60-80% similarity (orange)")
    low_similarity_count: int = Field(0, description="Words with 40-60% similarity (yellow)")

class HighlightResponse(BaseModel):
    """Response model for semantic word highlighting"""
    highlights: List[HighlightMatch] = Field([], description="List of word highlights")
    suspicious_text: str = Field(..., description="Original suspicious text")
    original_text: str = Field(..., description="Original text for reference")
    statistics: HighlightStatistics = Field(..., description="Highlighting statistics")
    highlighted_html: Optional[str] = Field(None, description="HTML with highlighted words")