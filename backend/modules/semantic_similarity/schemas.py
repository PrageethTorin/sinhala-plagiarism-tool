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